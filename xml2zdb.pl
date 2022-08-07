#!/usr/bin/perl
#
# Usage: ./xml2zdb.pl >ZDB-FILE
#
# This is a script to convert the `mem-*.xml` files into a (much simpler/
# smaller) ZDB (text database) output file. The script uses simple
# (regex-based) processing, which works well on the {boQwI'} data. (This is in
# no way a general XML parser, though.)
#
# The inverse of this command is `zdb2xml.pl`, which outputs XML data identical
# to the XML originally fed to this script (as far as possible, some things,
# such as uneven indentation in the original XML cannot be fully preserved).
#
# WORKFLOW
# ========
# The `xml2zdb.pl` and `zdb2xml.pl` are convenience scripts to simplify the
# database editing (for me, zrajm). Emacs (the editor I use) chokes on large
# XML files (which are not exactly human-friendly anyway) so in order to work
# around this, I do my editing in a plain text 'database' format of my own
# devising (this format is also used for the Klingonska Akademien Klingon
# dictionary, http://klingonska.org/dict/dict.zdb).
#
# Thus I first convert the {boQwI'} XML to ZDB format, using:
#
#     ./xml2zdb >mem.zdb
#
# After having done the any editing I desire, I convert the ZDB back to XML
# with the command:
#
#     ./zdb2xml <mem.zdb
#
# (This will overwrite the original {boQwI'} files, but keep backups of the
# previously existing files.)
#
# /zrajm [2022-08-05]

use warnings;
use strict;
use utf8;
binmode STDIN, ':utf8';
binmode STDOUT, ':utf8';

my @memparts = ('header', 'b', 'ch', 'D', 'gh', 'H', 'j', 'l', 'm', 'n', 'ng', 'p',
            'q', 'Q', 'r', 'S' ,'t', 'tlh', 'v', 'w', 'y', 'a', 'e', 'I', 'o',
            'u', 'suffixes', 'extra', 'examples', 'footer');

# FIXME: Instead of including all the fields in the outputted XML file,
# `xml2zdb.pl` should only export the selected fields. `zdb2xml.pl` should then
# (when regenerating the XML from ZDB) fill in values missing in the ZDB from
# the original XML. (This would make the .zbd file even smaller and easier to
# navigate/work with.)

# Commenting out any of the below lines in the `%field_name` causes
# corresponding fields to not be included in the outputted .zdb file.
my %field_name = (
    # XML name          # ZDB name
    '_id'               => '_id',
    'entry_name'        => 'tlh',
    'part_of_speech'    => 'pos',
    'definition'        => 'en',
    'definition_de'     => 'de',      ###
    'definition_fa'     => 'fa',      ###
    'definition_sv'     => 'sv',
    'definition_ru'     => 'ru',      ###
    'definition_zh_HK'  => 'hk',      ###
    'definition_pt'     => 'pt',      ###
    'definition_fi'     => 'fi',      ###
    'synonyms'          => 'syn',
    'antonyms'          => 'ant',
    'see_also'          => 'see',
    'notes'             => 'com-en',
    'notes_de'          => 'com-de',  ###
    'notes_fa'          => 'com-fa',  ###
    'notes_sv'          => 'com-sv',
    'notes_ru'          => 'com-ru',  ###
    'notes_zh_HK'       => 'com-hk',  ###
    'notes_pt'          => 'com-pt',  ###
    'notes_fi'          => 'com-fi',  ###
    'hidden_notes'      => 'hid',
    'components'        => 'part',
    'examples'          => 'cf-en',
    'examples_de'       => 'cf-de',   ###
    'examples_fa'       => 'cf-fa',   ###
    'examples_sv'       => 'cf-sv',
    'examples_ru'       => 'cf-ru',   ###
    'examples_zh_HK'    => 'cf-hk',   ###
    'examples_pt'       => 'cf-pt',   ###
    'examples_fi'       => 'cf-fi',   ###
    'search_tags'       => 'tag-en',
    'search_tags_de'    => 'tag-de',  ###
    'search_tags_fa'    => 'tag-fa',  ###
    'search_tags_sv'    => 'tag-sv',
    'search_tags_ru'    => 'tag-ru',  ###
    'search_tags_zh_HK' => 'tag-hk',  ###
    'search_tags_pt'    => 'tag-pt',  ###
    'search_tags_fi'    => 'tag-fi',  ###
    'source'            => 'ref',
);

sub format_field {
    my ($name, $value) = @_;
    if ($name eq 'tlh') {    # add {...} to 'tlh'
        $value = "{$value}";
    }
    $value = unescape_xml($value);
    $value = wordwrap($value, 71);
    $value =~ s/^/\t/gm;
    return "$name:$value\n";
}

sub format_comment {
    local ($_) = @_;
    $_ = unescape_xml($_);

    # If first char of comment is newline, then treat as preformatted
    # multi-line comment (stripping off any indentation it might have),
    # otherwise treat as single line comment (wordwrapping it).
    if (substr($_, 0, 1) eq "\n") {    # multi-line comment
        my ($indent) = m/\n(\h+)/;     #   get indent from 1st line
        s/^$indent//mg;                #   strip off of all lines
        s/(?<=\n)\h*$//;               #   strip any trailing whitespace
    } else {                           # single line comment
        $_ = wordwrap($_, 79);
    }
    return "/*$_*/\n";
}

sub read_file {
    my ($file) = @_;
    open(my $in, "<:utf8", $file) or die "Failed to open file '$file' for reading\n";
    return wantarray ? <$in> : join("", <$in>);
}

# This word wrapping is naïve and only works with writing systems which uses
# spaces for words separation (i.e. it does not work with the data in the
# 'zh_HK' field). It always affect any existing newlines, but wraps by
# replacing the last space in within the specified range with a newline. Space
# an the beginning or end of string is never wrapped.
sub wordwrap {
    (local $_, my $columns) = @_;

    # Insert '¶' before any existing newlines in the incoming XML, in the
    # original XML data, so that original newlines can restored when converting
    # back to XML (with 'zdb2xml').
    s/\n/¶\n/g;            # turn '\n' into '¶\n'

    s{(.{1,$columns})([ \n](?!$)|$)}{   # wordwrap
        $1 . ($2 eq ' ' ? "\n" : $2);
    }eg;
    return $_;
}

# Unescape XML entities (convert entity '&amp;' into plain char '&' etc).
{
    my %ent = (amp => '&', gt => '>', lt => '<');
    my $ent = qr/@{[ join '|', keys %ent ]}/;
    sub unescape_xml {
        local ($_) = @_;
        s/&($ent);/$ent{$1}/g;
        return $_;
    }
}

# Read all the XML files.
my $xml = do {
    my $i = 0;
    join('', map {
        my $file = sprintf 'mem-%02d-%s.xml', $i++, $_;
        ("<!--* FILE: $file *-->\n", read_file $file);
    } @memparts);
};

# For each '<table name="mem">...</table>' record.
my $standalone_comment = '';
my $field_out;
RECORD: while ($xml =~ m{(?:<!--(.*?)-->|<table\b[^>]*\bname="mem"[^>]*>(.*?)</table>)}sg) {
    my ($comment, $record) = ($1, $2);

    # Standalone (or record-level) comment. (This is outputted as a record
    # containing only a comment, i.e. separated from the previous and following
    # record by a blank line.)
    if ($comment) {
        print format_comment($comment);
        $standalone_comment = 1;
        next RECORD;
    }

    # For each <column name="...">...</column> field.
    $field_out = undef;
  FIELD: while ($record =~ m{(?:<!--(.*?)-->|<column name="([^"]*)"(?:/>|>(.*?)</column>))}sg) {
        my ($comment, $name, $value) = ($1, $2, $3);

        # If preceded by a standalone comment, add a blank line before the
        # record.
        if ($standalone_comment) {
            $standalone_comment = '';
            print "\n";
        }

        # Field-level comment (i.e. a comment inside a record).
        if ($comment) {
            print "$field_out:\t\n" if defined $field_out;
            print format_comment($comment);
            next FIELD;
        }

        # Field and value.
        my $name_out = $field_name{$name};
        $field_out = $name_out;
        if ($value ne '' and $name_out) {
            print format_field($name_out, $value);
            $field_out = undef;
        }
    }
    print "\n";
}

#[eof]
