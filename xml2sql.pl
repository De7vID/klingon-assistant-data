#!/usr/bin/perl
use utf8;

# use modules
use File::Slurp;
use XML::Simple;

# output Unicode
binmode(STDOUT, ":utf8");

# create xml object
$xml = new XML::Simple;

# read xml file
$sm_export = read_file('mem.xml');

# do substitutions to make it ready for conversion
$sm_export =~ s/\s*<!--.*?-->//sg;
$sm_export =~ s/<table name="mem">(.*?)<\/table>/<mem>\1<\/mem>/sg;
$sm_export =~ s/<column name="(.*?)">(.*?)<\/column>/<\1>\2<\/\1>/sg;
$sm_export =~ s/'/''/g;
open (my $sm_export_file, '>', 'mem_processed.xml') or die "Failed to write processed xml.";
print $sm_export_file $sm_export;
close $sm_export_file;

# convert processed xml file to xml
$data = $xml->XMLin($sm_export, suppressempty => '');

# print sql file header
print "PRAGMA foreign_keys=OFF;\n".
      "BEGIN TRANSACTION;\n".
      "CREATE TABLE IF NOT EXISTS \"android_metadata\" (\"locale\" TEXT DEFAULT 'en_US');\n".
      "INSERT INTO android_metadata VALUES('en_US');\n".
      "CREATE TABLE IF NOT EXISTS \"mem\" (\"_id\" INTEGER PRIMARY KEY,\"entry_name\" TEXT,\"part_of_speech\" TEXT,\"definition\" TEXT,\"synonyms\" TEXT,\"antonyms\" TEXT,\"see_also\" TEXT,\"notes\" TEXT,\"hidden_notes\" TEXT,\"components\" TEXT,\"examples\" TEXT,\"search_tags\" TEXT,\"source\" TEXT,\"definition_de\" TEXT,\"notes_de\" TEXT,\"examples_de\" TEXT,\"search_tags_de\" TEXT,\"definition_fa\" TEXT,\"notes_fa\" TEXT,\"examples_fa\" TEXT,\"search_tags_fa\" TEXT,\"definition_sv\" TEXT,\"notes_sv\" TEXT,\"examples_sv\" TEXT,\"search_tags_sv\" TEXT,\"definition_ru\" TEXT,\"notes_ru\" TEXT,\"examples_ru\" TEXT,\"search_tags_ru\" TEXT,\"definition_zh_HK\" TEXT,\"notes_zh_HK\" TEXT,\"examples_zh_HK\" TEXT,\"search_tags_zh_HK\" TEXT,\"definition_pt\" TEXT,\"notes_pt\" TEXT,\"examples_pt\" TEXT,\"search_tags_pt\" TEXT DEFAULT \"\");\n";

# Regex to check "en" language fields.
$valid_en = qr/^[A-Za-z0-9 '":;,.\-?!_\/\()@=%&*{}\[\]<>▶\nàéü+×÷神舟]*$/;

# Language tags.
@langs = qw(de fa ru sv zh-HK pt);

# cycle through and print the entries
foreach $e (@{$data->{database}->{mem}})
{
    # Sanity check for "en" fields.
    if ($e->{entry_name} ne "boQwI''" && $e->{entry_name} ne "QIch wab Ho''DoS") {
        if ("$e->{definition}" !~ "$valid_en") {
            print STDERR "Non-staniard characters: ", "$e->{definition}", "\n";
        }
        if ("$e->{notes}" !~ "$valid_en") {
            print STDERR "Non-standard characters: ", "$e->{notes}", "\n";
        }
        if ("$e->{examples}" !~ "$valid_en") {
            print STDERR "Non-standard characters: ", "$e->{examples}", "\n";
        }
        if ("$e->{search_tags}" !~ "$valid_en") {
            print STDERR "Non-standard characters: ", "$e->{search_tags}", "\n";
        }
    }

    # Check that non-"en" examples do not duplicate "en" fields.
    foreach $lang (@langs) {
        if ("$e->{examples}" ne "" && $e->{"examples_$lang"} eq "$e->{examples}") {
            print STDERR "Duplicated examples (", $lang, "): ", "$e->{examples}", "\n";
        }
    }

    # Output a row.
    print "INSERT INTO \"mem\" VALUES(";
    print $e->{_id}, ",'";
    print $e->{entry_name}, "','";
    print $e->{part_of_speech}, "','";
    print $e->{definition}, "','";
    print $e->{synonyms}, "','";
    print $e->{antonyms}, "','";
    print $e->{see_also}, "','";
    print $e->{notes}, "','";
    print $e->{hidden_notes}, "','";
    print $e->{components}, "','";
    print $e->{examples}, "','";
    print $e->{search_tags}, "','";
    print $e->{source}, "','";
    print $e->{definition_de}, "','";
    print $e->{notes_de}, "','";
    print $e->{examples_de}, "','";
    print $e->{search_tags_de}, "','";
    print $e->{definition_fa}, "','";
    print $e->{notes_fa}, "','";
    print $e->{examples_fa}, "','";
    print $e->{search_tags_fa}, "','";
    print $e->{definition_sv}, "','";
    print $e->{notes_sv}, "','";
    print $e->{examples_sv}, "','";
    print $e->{search_tags_sv}, "','";
    print $e->{definition_ru}, "','";
    print $e->{notes_ru}, "','";
    print $e->{examples_ru}, "','";
    print $e->{search_tags_ru}, "','";
    print $e->{definition_zh_HK}, "','";
    print $e->{notes_zh_HK}, "','";
    print $e->{examples_zh_HK}, "','";
    print $e->{search_tags_zh_HK}, "','";
    print $e->{definition_pt}, "','";
    print $e->{notes_pt}, "','";
    print $e->{examples_pt}, "','";
    print $e->{search_tags_pt}, "');\n";
}

# print sql file footer
print "COMMIT;\n";
