#!/usr/bin/perl

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

# convert processed xml file to xml
$data = $xml->XMLin($sm_export, suppressempty => '');

# print sql file header
print "PRAGMA foreign_keys=OFF;\n".
      "BEGIN TRANSACTION;\n".
      "CREATE TABLE \"android_metadata\" (\"locale\" TEXT DEFAULT 'en_US');\n".
      "INSERT INTO \"android_metadata\" VALUES('en_US');\n".
      "CREATE TABLE \"mem\" (\"_id\" INTEGER PRIMARY KEY ,\"entry_name\" TEXT,\"part_of_speech\" TEXT,\"definition\" TEXT,\"synonyms\" TEXT,\"antonyms\" TEXT,\"see_also\" TEXT,\"notes\" TEXT,\"hidden_notes\" TEXT,\"components\" TEXT,\"examples\" TEXT,\"search_tags\" TEXT,\"source\" TEXT,\"definition_de\" TEXT,\"notes_de\" TEXT,\"examples_de\" TEXT,\"search_tags_de\" TEXT DEFAULT \"\");\n";

# cycle through and print the entries
foreach $e (@{$data->{database}->{mem}})
{
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
    print $e->{search_tags_de}, "');\n";
}

# print sql file footer
print "COMMIT;\n";
