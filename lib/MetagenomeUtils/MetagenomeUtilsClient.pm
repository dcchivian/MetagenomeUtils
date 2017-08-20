package MetagenomeUtils::MetagenomeUtilsClient;

use JSON::RPC::Client;
use POSIX;
use strict;
use Data::Dumper;
use URI;
use Bio::KBase::Exceptions;
my $get_time = sub { time, 0 };
eval {
    require Time::HiRes;
    $get_time = sub { Time::HiRes::gettimeofday() };
};

use Bio::KBase::AuthToken;

# Client version should match Impl version
# This is a Semantic Version number,
# http://semver.org
our $VERSION = "0.1.0";

=head1 NAME

MetagenomeUtils::MetagenomeUtilsClient

=head1 DESCRIPTION


A KBase module for interacting with Metagenomic data in KBase


=cut

sub new
{
    my($class, $url, @args) = @_;
    

    my $self = {
	client => MetagenomeUtils::MetagenomeUtilsClient::RpcClient->new,
	url => $url,
	headers => [],
    };

    chomp($self->{hostname} = `hostname`);
    $self->{hostname} ||= 'unknown-host';

    #
    # Set up for propagating KBRPC_TAG and KBRPC_METADATA environment variables through
    # to invoked services. If these values are not set, we create a new tag
    # and a metadata field with basic information about the invoking script.
    #
    if ($ENV{KBRPC_TAG})
    {
	$self->{kbrpc_tag} = $ENV{KBRPC_TAG};
    }
    else
    {
	my ($t, $us) = &$get_time();
	$us = sprintf("%06d", $us);
	my $ts = strftime("%Y-%m-%dT%H:%M:%S.${us}Z", gmtime $t);
	$self->{kbrpc_tag} = "C:$0:$self->{hostname}:$$:$ts";
    }
    push(@{$self->{headers}}, 'Kbrpc-Tag', $self->{kbrpc_tag});

    if ($ENV{KBRPC_METADATA})
    {
	$self->{kbrpc_metadata} = $ENV{KBRPC_METADATA};
	push(@{$self->{headers}}, 'Kbrpc-Metadata', $self->{kbrpc_metadata});
    }

    if ($ENV{KBRPC_ERROR_DEST})
    {
	$self->{kbrpc_error_dest} = $ENV{KBRPC_ERROR_DEST};
	push(@{$self->{headers}}, 'Kbrpc-Errordest', $self->{kbrpc_error_dest});
    }

    #
    # This module requires authentication.
    #
    # We create an auth token, passing through the arguments that we were (hopefully) given.

    {
	my %arg_hash2 = @args;
	if (exists $arg_hash2{"token"}) {
	    $self->{token} = $arg_hash2{"token"};
	} elsif (exists $arg_hash2{"user_id"}) {
	    my $token = Bio::KBase::AuthToken->new(@args);
	    if (!$token->error_message) {
	        $self->{token} = $token->token;
	    }
	}
	
	if (exists $self->{token})
	{
	    $self->{client}->{token} = $self->{token};
	}
    }

    my $ua = $self->{client}->ua;	 
    my $timeout = $ENV{CDMI_TIMEOUT} || (30 * 60);	 
    $ua->timeout($timeout);
    bless $self, $class;
    #    $self->_validate_version();
    return $self;
}




=head2 file_to_binned_contigs

  $returnVal = $obj->file_to_binned_contigs($params)

=over 4

=item Parameter and return types

=begin html

<pre>
$params is a MetagenomeUtils.FileToBinnedContigParams
$returnVal is a MetagenomeUtils.FileToBinnedContigResult
FileToBinnedContigParams is a reference to a hash where the following keys are defined:
	file_directory has a value which is a string
	assembly_ref has a value which is a MetagenomeUtils.obj_ref
	binned_contig_name has a value which is a string
	workspace_name has a value which is a string
obj_ref is a string
FileToBinnedContigResult is a reference to a hash where the following keys are defined:
	binned_contig_obj_ref has a value which is a MetagenomeUtils.obj_ref

</pre>

=end html

=begin text

$params is a MetagenomeUtils.FileToBinnedContigParams
$returnVal is a MetagenomeUtils.FileToBinnedContigResult
FileToBinnedContigParams is a reference to a hash where the following keys are defined:
	file_directory has a value which is a string
	assembly_ref has a value which is a MetagenomeUtils.obj_ref
	binned_contig_name has a value which is a string
	workspace_name has a value which is a string
obj_ref is a string
FileToBinnedContigResult is a reference to a hash where the following keys are defined:
	binned_contig_obj_ref has a value which is a MetagenomeUtils.obj_ref


=end text

=item Description

file_to_binned_contigs: Generating BinnedContigs ojbect from files

input params:
file_directory: file directory containing compressed/unpacked contig file(s) to build BinnedContig object
assembly_ref: Metagenome assembly object reference
binned_contig_name: BinnedContig object name
workspace_name: the name/id of the workspace it gets saved to

return params:
binned_contig_obj_ref: generated result BinnedContig object reference

=back

=cut

 sub file_to_binned_contigs
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function file_to_binned_contigs (received $n, expecting 1)");
    }
    {
	my($params) = @args;

	my @_bad_arguments;
        (ref($params) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument 1 \"params\" (value was \"$params\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to file_to_binned_contigs:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'file_to_binned_contigs');
	}
    }

    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
	    method => "MetagenomeUtils.file_to_binned_contigs",
	    params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'file_to_binned_contigs',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method file_to_binned_contigs",
					    status_line => $self->{client}->status_line,
					    method_name => 'file_to_binned_contigs',
				       );
    }
}
 


=head2 binned_contigs_to_file

  $returnVal = $obj->binned_contigs_to_file($params)

=over 4

=item Parameter and return types

=begin html

<pre>
$params is a MetagenomeUtils.ExportParams
$returnVal is a MetagenomeUtils.ExportOutput
ExportParams is a reference to a hash where the following keys are defined:
	input_ref has a value which is a string
	save_to_shock has a value which is a MetagenomeUtils.boolean
boolean is an int
ExportOutput is a reference to a hash where the following keys are defined:
	shock_id has a value which is a string
	bin_file_directory has a value which is a string

</pre>

=end html

=begin text

$params is a MetagenomeUtils.ExportParams
$returnVal is a MetagenomeUtils.ExportOutput
ExportParams is a reference to a hash where the following keys are defined:
	input_ref has a value which is a string
	save_to_shock has a value which is a MetagenomeUtils.boolean
boolean is an int
ExportOutput is a reference to a hash where the following keys are defined:
	shock_id has a value which is a string
	bin_file_directory has a value which is a string


=end text

=item Description

binned_contigs_to_file: Convert BinnedContig object to fasta files and pack them to shock

required params:
input_ref: BinnedContig object reference

optional params:
save_to_shock: saving result bin files to shock. default to True

return params:
shock_id: saved packed file shock id (None if save_to_shock is set to False)
bin_file_directory: directory that contains all bin files

=back

=cut

 sub binned_contigs_to_file
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function binned_contigs_to_file (received $n, expecting 1)");
    }
    {
	my($params) = @args;

	my @_bad_arguments;
        (ref($params) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument 1 \"params\" (value was \"$params\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to binned_contigs_to_file:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'binned_contigs_to_file');
	}
    }

    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
	    method => "MetagenomeUtils.binned_contigs_to_file",
	    params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'binned_contigs_to_file',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method binned_contigs_to_file",
					    status_line => $self->{client}->status_line,
					    method_name => 'binned_contigs_to_file',
				       );
    }
}
 


=head2 extract_binned_contigs_as_assembly

  $returnVal = $obj->extract_binned_contigs_as_assembly($params)

=over 4

=item Parameter and return types

=begin html

<pre>
$params is a MetagenomeUtils.ExtractBinAsAssemblyParams
$returnVal is a MetagenomeUtils.ExtractBinAsAssemblyResult
ExtractBinAsAssemblyParams is a reference to a hash where the following keys are defined:
	binned_contig_obj_ref has a value which is a MetagenomeUtils.obj_ref
	extracted_assemblies has a value which is a reference to a list where each element is a reference to a hash where the key is a string and the value is a string
	workspace_name has a value which is a string
obj_ref is a string
ExtractBinAsAssemblyResult is a reference to a hash where the following keys are defined:
	assembly_ref_list has a value which is a reference to a list where each element is a MetagenomeUtils.obj_ref
	report_name has a value which is a string
	report_ref has a value which is a string

</pre>

=end html

=begin text

$params is a MetagenomeUtils.ExtractBinAsAssemblyParams
$returnVal is a MetagenomeUtils.ExtractBinAsAssemblyResult
ExtractBinAsAssemblyParams is a reference to a hash where the following keys are defined:
	binned_contig_obj_ref has a value which is a MetagenomeUtils.obj_ref
	extracted_assemblies has a value which is a reference to a list where each element is a reference to a hash where the key is a string and the value is a string
	workspace_name has a value which is a string
obj_ref is a string
ExtractBinAsAssemblyResult is a reference to a hash where the following keys are defined:
	assembly_ref_list has a value which is a reference to a list where each element is a MetagenomeUtils.obj_ref
	report_name has a value which is a string
	report_ref has a value which is a string


=end text

=item Description

extract_binned_contigs_as_assembly: extract one/multiple Bins from BinnedContigs as Assembly object

input params:
binned_contig_obj_ref: BinnedContig object reference
extracted_assemblies: a list of:
      bin_id: target bin id to be extracted
      assembly_suffix: suffix appended to assembly object name
workspace_name: the name of the workspace it gets saved to

return params:
assembly_ref_list: list of generated result Assembly object reference
report_name: report name generated by KBaseReport
report_ref: report reference generated by KBaseReport

=back

=cut

 sub extract_binned_contigs_as_assembly
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function extract_binned_contigs_as_assembly (received $n, expecting 1)");
    }
    {
	my($params) = @args;

	my @_bad_arguments;
        (ref($params) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument 1 \"params\" (value was \"$params\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to extract_binned_contigs_as_assembly:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'extract_binned_contigs_as_assembly');
	}
    }

    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
	    method => "MetagenomeUtils.extract_binned_contigs_as_assembly",
	    params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'extract_binned_contigs_as_assembly',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method extract_binned_contigs_as_assembly",
					    status_line => $self->{client}->status_line,
					    method_name => 'extract_binned_contigs_as_assembly',
				       );
    }
}
 


=head2 remove_bins_from_binned_contig

  $returnVal = $obj->remove_bins_from_binned_contig($params)

=over 4

=item Parameter and return types

=begin html

<pre>
$params is a MetagenomeUtils.RemoveBinsParams
$returnVal is a MetagenomeUtils.RemoveBinsResult
RemoveBinsParams is a reference to a hash where the following keys are defined:
	old_binned_contig_ref has a value which is a MetagenomeUtils.obj_ref
	bins_to_remove has a value which is a reference to a list where each element is a string
	output_binned_contig_name has a value which is a string
	workspace_name has a value which is a string
obj_ref is a string
RemoveBinsResult is a reference to a hash where the following keys are defined:
	new_binned_contig_ref has a value which is a MetagenomeUtils.obj_ref

</pre>

=end html

=begin text

$params is a MetagenomeUtils.RemoveBinsParams
$returnVal is a MetagenomeUtils.RemoveBinsResult
RemoveBinsParams is a reference to a hash where the following keys are defined:
	old_binned_contig_ref has a value which is a MetagenomeUtils.obj_ref
	bins_to_remove has a value which is a reference to a list where each element is a string
	output_binned_contig_name has a value which is a string
	workspace_name has a value which is a string
obj_ref is a string
RemoveBinsResult is a reference to a hash where the following keys are defined:
	new_binned_contig_ref has a value which is a MetagenomeUtils.obj_ref


=end text

=item Description

remove_bins_from_binned_contig: remove a list of bins from BinnedContig object

input params:
old_binned_contig_ref: Original BinnedContig object reference
bins_to_remove: a list of bin ids to be removed
output_binned_contig_name: Name for the output BinnedContigs object
workspace_name: the name of the workspace new object gets saved to

return params:
new_binned_contig_ref: newly created BinnedContig object referece

=back

=cut

 sub remove_bins_from_binned_contig
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function remove_bins_from_binned_contig (received $n, expecting 1)");
    }
    {
	my($params) = @args;

	my @_bad_arguments;
        (ref($params) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument 1 \"params\" (value was \"$params\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to remove_bins_from_binned_contig:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'remove_bins_from_binned_contig');
	}
    }

    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
	    method => "MetagenomeUtils.remove_bins_from_binned_contig",
	    params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'remove_bins_from_binned_contig',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method remove_bins_from_binned_contig",
					    status_line => $self->{client}->status_line,
					    method_name => 'remove_bins_from_binned_contig',
				       );
    }
}
 


=head2 merge_bins_from_binned_contig

  $returnVal = $obj->merge_bins_from_binned_contig($params)

=over 4

=item Parameter and return types

=begin html

<pre>
$params is a MetagenomeUtils.MergeBinsParams
$returnVal is a MetagenomeUtils.MergeBinsResult
MergeBinsParams is a reference to a hash where the following keys are defined:
	old_binned_contig_ref has a value which is a MetagenomeUtils.obj_ref
	bin_merges has a value which is a reference to a list where each element is a reference to a hash where the key is a string and the value is a string
	output_binned_contig_name has a value which is a string
	workspace_name has a value which is a string
obj_ref is a string
MergeBinsResult is a reference to a hash where the following keys are defined:
	new_binned_contig_ref has a value which is a MetagenomeUtils.obj_ref

</pre>

=end html

=begin text

$params is a MetagenomeUtils.MergeBinsParams
$returnVal is a MetagenomeUtils.MergeBinsResult
MergeBinsParams is a reference to a hash where the following keys are defined:
	old_binned_contig_ref has a value which is a MetagenomeUtils.obj_ref
	bin_merges has a value which is a reference to a list where each element is a reference to a hash where the key is a string and the value is a string
	output_binned_contig_name has a value which is a string
	workspace_name has a value which is a string
obj_ref is a string
MergeBinsResult is a reference to a hash where the following keys are defined:
	new_binned_contig_ref has a value which is a MetagenomeUtils.obj_ref


=end text

=item Description

merge_bins_from_binned_contig: merge a list of bins from BinnedContig object

input params:
old_binned_contig_ref: Original BinnedContig object reference
bin_merges: a list of bin merges dicts
  new_bin_id: newly created bin id
  bin_to_merge: list of bins to merge
output_binned_contig_name: Name for the output BinnedContigs object
workspace_name: the name of the workspace new object gets saved to

return params:
new_binned_contig_ref: newly created BinnedContig object referece

=back

=cut

 sub merge_bins_from_binned_contig
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function merge_bins_from_binned_contig (received $n, expecting 1)");
    }
    {
	my($params) = @args;

	my @_bad_arguments;
        (ref($params) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument 1 \"params\" (value was \"$params\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to merge_bins_from_binned_contig:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'merge_bins_from_binned_contig');
	}
    }

    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
	    method => "MetagenomeUtils.merge_bins_from_binned_contig",
	    params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'merge_bins_from_binned_contig',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method merge_bins_from_binned_contig",
					    status_line => $self->{client}->status_line,
					    method_name => 'merge_bins_from_binned_contig',
				       );
    }
}
 


=head2 edit_bins_from_binned_contig

  $returnVal = $obj->edit_bins_from_binned_contig($params)

=over 4

=item Parameter and return types

=begin html

<pre>
$params is a MetagenomeUtils.EditBinsParams
$returnVal is a MetagenomeUtils.EditBinsResult
EditBinsParams is a reference to a hash where the following keys are defined:
	old_binned_contig_ref has a value which is a MetagenomeUtils.obj_ref
	bins_to_remove has a value which is a reference to a list where each element is a string
	bin_merges has a value which is a reference to a list where each element is a reference to a hash where the key is a string and the value is a string
	output_binned_contig_name has a value which is a string
	workspace_name has a value which is a string
obj_ref is a string
EditBinsResult is a reference to a hash where the following keys are defined:
	new_binned_contig_ref has a value which is a MetagenomeUtils.obj_ref
	report_name has a value which is a string
	report_ref has a value which is a string

</pre>

=end html

=begin text

$params is a MetagenomeUtils.EditBinsParams
$returnVal is a MetagenomeUtils.EditBinsResult
EditBinsParams is a reference to a hash where the following keys are defined:
	old_binned_contig_ref has a value which is a MetagenomeUtils.obj_ref
	bins_to_remove has a value which is a reference to a list where each element is a string
	bin_merges has a value which is a reference to a list where each element is a reference to a hash where the key is a string and the value is a string
	output_binned_contig_name has a value which is a string
	workspace_name has a value which is a string
obj_ref is a string
EditBinsResult is a reference to a hash where the following keys are defined:
	new_binned_contig_ref has a value which is a MetagenomeUtils.obj_ref
	report_name has a value which is a string
	report_ref has a value which is a string


=end text

=item Description

edit_bins_from_binned_contig: merge/remove a list of bins from BinnedContig object
a wrapper method of:
merge_bins_from_binned_contig
remove_bins_from_binned_contig


input params:
old_binned_contig_ref: Original BinnedContig object reference
bins_to_remove: a list of bin ids to be removed
bin_merges: a list of bin merges dicts
  new_bin_id: newly created bin id
  bin_to_merge: list of bins to merge
output_binned_contig_name: Name for the output BinnedContigs object
workspace_name: the name of the workspace new object gets saved to

return params:
new_binned_contig_ref: newly created BinnedContig object referece
report_name: report name generated by KBaseReport
report_ref: report reference generated by KBaseReport

=back

=cut

 sub edit_bins_from_binned_contig
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function edit_bins_from_binned_contig (received $n, expecting 1)");
    }
    {
	my($params) = @args;

	my @_bad_arguments;
        (ref($params) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument 1 \"params\" (value was \"$params\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to edit_bins_from_binned_contig:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'edit_bins_from_binned_contig');
	}
    }

    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
	    method => "MetagenomeUtils.edit_bins_from_binned_contig",
	    params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'edit_bins_from_binned_contig',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method edit_bins_from_binned_contig",
					    status_line => $self->{client}->status_line,
					    method_name => 'edit_bins_from_binned_contig',
				       );
    }
}
 
  
sub status
{
    my($self, @args) = @_;
    if ((my $n = @args) != 0) {
        Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
                                   "Invalid argument count for function status (received $n, expecting 0)");
    }
    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
        method => "MetagenomeUtils.status",
        params => \@args,
    });
    if ($result) {
        if ($result->is_error) {
            Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
                           code => $result->content->{error}->{code},
                           method_name => 'status',
                           data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
                          );
        } else {
            return wantarray ? @{$result->result} : $result->result->[0];
        }
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method status",
                        status_line => $self->{client}->status_line,
                        method_name => 'status',
                       );
    }
}
   

sub version {
    my ($self) = @_;
    my $result = $self->{client}->call($self->{url}, $self->{headers}, {
        method => "MetagenomeUtils.version",
        params => [],
    });
    if ($result) {
        if ($result->is_error) {
            Bio::KBase::Exceptions::JSONRPC->throw(
                error => $result->error_message,
                code => $result->content->{code},
                method_name => 'edit_bins_from_binned_contig',
            );
        } else {
            return wantarray ? @{$result->result} : $result->result->[0];
        }
    } else {
        Bio::KBase::Exceptions::HTTP->throw(
            error => "Error invoking method edit_bins_from_binned_contig",
            status_line => $self->{client}->status_line,
            method_name => 'edit_bins_from_binned_contig',
        );
    }
}

sub _validate_version {
    my ($self) = @_;
    my $svr_version = $self->version();
    my $client_version = $VERSION;
    my ($cMajor, $cMinor) = split(/\./, $client_version);
    my ($sMajor, $sMinor) = split(/\./, $svr_version);
    if ($sMajor != $cMajor) {
        Bio::KBase::Exceptions::ClientServerIncompatible->throw(
            error => "Major version numbers differ.",
            server_version => $svr_version,
            client_version => $client_version
        );
    }
    if ($sMinor < $cMinor) {
        Bio::KBase::Exceptions::ClientServerIncompatible->throw(
            error => "Client minor version greater than Server minor version.",
            server_version => $svr_version,
            client_version => $client_version
        );
    }
    if ($sMinor > $cMinor) {
        warn "New client version available for MetagenomeUtils::MetagenomeUtilsClient\n";
    }
    if ($sMajor == 0) {
        warn "MetagenomeUtils::MetagenomeUtilsClient version is $svr_version. API subject to change.\n";
    }
}

=head1 TYPES



=head2 obj_ref

=over 4



=item Description

An X/Y/Z style reference


=item Definition

=begin html

<pre>
a string
</pre>

=end html

=begin text

a string

=end text

=back



=head2 boolean

=over 4



=item Description

A boolean - 0 for false, 1 for true.
@range (0, 1)


=item Definition

=begin html

<pre>
an int
</pre>

=end html

=begin text

an int

=end text

=back



=head2 FileToBinnedContigParams

=over 4



=item Description

file_directory: file directory containing compressed/unpacked contig file(s) to build BinnedContig object
assembly_ref: Metagenome assembly object reference
binned_contig_name: BinnedContig object name
workspace_name: the name/id of the workspace it gets saved to


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
file_directory has a value which is a string
assembly_ref has a value which is a MetagenomeUtils.obj_ref
binned_contig_name has a value which is a string
workspace_name has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
file_directory has a value which is a string
assembly_ref has a value which is a MetagenomeUtils.obj_ref
binned_contig_name has a value which is a string
workspace_name has a value which is a string


=end text

=back



=head2 FileToBinnedContigResult

=over 4



=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
binned_contig_obj_ref has a value which is a MetagenomeUtils.obj_ref

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
binned_contig_obj_ref has a value which is a MetagenomeUtils.obj_ref


=end text

=back



=head2 ExportParams

=over 4



=item Description

input_ref: BinnedContig object reference

optional params:
save_to_shock: saving result bin files to shock. default to True


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
input_ref has a value which is a string
save_to_shock has a value which is a MetagenomeUtils.boolean

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
input_ref has a value which is a string
save_to_shock has a value which is a MetagenomeUtils.boolean


=end text

=back



=head2 ExportOutput

=over 4



=item Description

shock_id: saved packed file shock id
bin_file_directory: directory that contains all bin files


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
shock_id has a value which is a string
bin_file_directory has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
shock_id has a value which is a string
bin_file_directory has a value which is a string


=end text

=back



=head2 ExtractBinAsAssemblyParams

=over 4



=item Description

binned_contig_obj_ref: BinnedContig object reference
extracted_assemblies: a list of:
      bin_id: target bin id to be extracted
      assembly_suffix: suffix appended to assembly object name
workspace_name: the name of the workspace it gets saved to


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
binned_contig_obj_ref has a value which is a MetagenomeUtils.obj_ref
extracted_assemblies has a value which is a reference to a list where each element is a reference to a hash where the key is a string and the value is a string
workspace_name has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
binned_contig_obj_ref has a value which is a MetagenomeUtils.obj_ref
extracted_assemblies has a value which is a reference to a list where each element is a reference to a hash where the key is a string and the value is a string
workspace_name has a value which is a string


=end text

=back



=head2 ExtractBinAsAssemblyResult

=over 4



=item Description

assembly_ref_list: list of generated Assembly object reference
report_name: report name generated by KBaseReport
report_ref: report reference generated by KBaseReport


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
assembly_ref_list has a value which is a reference to a list where each element is a MetagenomeUtils.obj_ref
report_name has a value which is a string
report_ref has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
assembly_ref_list has a value which is a reference to a list where each element is a MetagenomeUtils.obj_ref
report_name has a value which is a string
report_ref has a value which is a string


=end text

=back



=head2 RemoveBinsParams

=over 4



=item Description

old_binned_contig_ref: Original BinnedContig object reference
bins_to_remove: a list of bin ids to be removed
output_binned_contig_name: Name for the output BinnedContigs object
workspace_name: the name of the workspace new object gets saved to


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
old_binned_contig_ref has a value which is a MetagenomeUtils.obj_ref
bins_to_remove has a value which is a reference to a list where each element is a string
output_binned_contig_name has a value which is a string
workspace_name has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
old_binned_contig_ref has a value which is a MetagenomeUtils.obj_ref
bins_to_remove has a value which is a reference to a list where each element is a string
output_binned_contig_name has a value which is a string
workspace_name has a value which is a string


=end text

=back



=head2 RemoveBinsResult

=over 4



=item Description

new_binned_contig_ref: newly created BinnedContig object referece
report_name: report name generated by KBaseReport
report_ref: report reference generated by KBaseReport


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
new_binned_contig_ref has a value which is a MetagenomeUtils.obj_ref

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
new_binned_contig_ref has a value which is a MetagenomeUtils.obj_ref


=end text

=back



=head2 MergeBinsParams

=over 4



=item Description

old_binned_contig_ref: Original BinnedContig object reference
bin_merges: a list of bin merges dicts
  new_bin_id: newly created bin id
  bin_to_merge: list of bins to merge
output_binned_contig_name: Name for the output BinnedContigs object
workspace_name: the name of the workspace new object gets saved to


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
old_binned_contig_ref has a value which is a MetagenomeUtils.obj_ref
bin_merges has a value which is a reference to a list where each element is a reference to a hash where the key is a string and the value is a string
output_binned_contig_name has a value which is a string
workspace_name has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
old_binned_contig_ref has a value which is a MetagenomeUtils.obj_ref
bin_merges has a value which is a reference to a list where each element is a reference to a hash where the key is a string and the value is a string
output_binned_contig_name has a value which is a string
workspace_name has a value which is a string


=end text

=back



=head2 MergeBinsResult

=over 4



=item Description

new_binned_contig_ref: newly created BinnedContig object referece


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
new_binned_contig_ref has a value which is a MetagenomeUtils.obj_ref

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
new_binned_contig_ref has a value which is a MetagenomeUtils.obj_ref


=end text

=back



=head2 EditBinsParams

=over 4



=item Description

old_binned_contig_ref: Original BinnedContig object reference
bins_to_remove: a list of bin ids to be removed
bin_merges: a list of bin merges dicts
  new_bin_id: newly created bin id
  bin_to_merge: list of bins to merge
output_binned_contig_name: Name for the output BinnedContigs object
workspace_name: the name of the workspace new object gets saved to


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
old_binned_contig_ref has a value which is a MetagenomeUtils.obj_ref
bins_to_remove has a value which is a reference to a list where each element is a string
bin_merges has a value which is a reference to a list where each element is a reference to a hash where the key is a string and the value is a string
output_binned_contig_name has a value which is a string
workspace_name has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
old_binned_contig_ref has a value which is a MetagenomeUtils.obj_ref
bins_to_remove has a value which is a reference to a list where each element is a string
bin_merges has a value which is a reference to a list where each element is a reference to a hash where the key is a string and the value is a string
output_binned_contig_name has a value which is a string
workspace_name has a value which is a string


=end text

=back



=head2 EditBinsResult

=over 4



=item Description

new_binned_contig_ref: newly created BinnedContig object referece
report_name: report name generated by KBaseReport
report_ref: report reference generated by KBaseReport


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
new_binned_contig_ref has a value which is a MetagenomeUtils.obj_ref
report_name has a value which is a string
report_ref has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
new_binned_contig_ref has a value which is a MetagenomeUtils.obj_ref
report_name has a value which is a string
report_ref has a value which is a string


=end text

=back



=cut

package MetagenomeUtils::MetagenomeUtilsClient::RpcClient;
use base 'JSON::RPC::Client';
use POSIX;
use strict;

#
# Override JSON::RPC::Client::call because it doesn't handle error returns properly.
#

sub call {
    my ($self, $uri, $headers, $obj) = @_;
    my $result;


    {
	if ($uri =~ /\?/) {
	    $result = $self->_get($uri);
	}
	else {
	    Carp::croak "not hashref." unless (ref $obj eq 'HASH');
	    $result = $self->_post($uri, $headers, $obj);
	}

    }

    my $service = $obj->{method} =~ /^system\./ if ( $obj );

    $self->status_line($result->status_line);

    if ($result->is_success) {

        return unless($result->content); # notification?

        if ($service) {
            return JSON::RPC::ServiceObject->new($result, $self->json);
        }

        return JSON::RPC::ReturnObject->new($result, $self->json);
    }
    elsif ($result->content_type eq 'application/json')
    {
        return JSON::RPC::ReturnObject->new($result, $self->json);
    }
    else {
        return;
    }
}


sub _post {
    my ($self, $uri, $headers, $obj) = @_;
    my $json = $self->json;

    $obj->{version} ||= $self->{version} || '1.1';

    if ($obj->{version} eq '1.0') {
        delete $obj->{version};
        if (exists $obj->{id}) {
            $self->id($obj->{id}) if ($obj->{id}); # if undef, it is notification.
        }
        else {
            $obj->{id} = $self->id || ($self->id('JSON::RPC::Client'));
        }
    }
    else {
        # $obj->{id} = $self->id if (defined $self->id);
	# Assign a random number to the id if one hasn't been set
	$obj->{id} = (defined $self->id) ? $self->id : substr(rand(),2);
    }

    my $content = $json->encode($obj);

    $self->ua->post(
        $uri,
        Content_Type   => $self->{content_type},
        Content        => $content,
        Accept         => 'application/json',
	@$headers,
	($self->{token} ? (Authorization => $self->{token}) : ()),
    );
}



1;
