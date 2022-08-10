Command-Line Interface
======================

write-table-to-pickle
---------------------

::

  write-table-to-pickle -h
  usage: write-table-to-pickle [-h] [-v VERBOSE] [--config CONFIG] [--print-args PRINT_ARGS] [-i IN_TYPE] [-o OUT_TYPE] rspecifier value_out [key_out]
  
  Write a kaldi table to pickle file(s)
  
      The inverse is write-pickle-to-table
      
  
  positional arguments:
    rspecifier            The table to read
    value_out             A path to write (key,value) pairs to, or just values if key_out was set. If it ends in ".gz", the file will be gzipped
    key_out               A path to write keys to. If it ends in ".gz", the file will be gzipped
  
  optional arguments:
    -h, --help            show this help message and exit
    -v VERBOSE, --verbose VERBOSE
                          Verbose level (higher->more logging)
    --config CONFIG
    --print-args PRINT_ARGS
    -i IN_TYPE, --in-type IN_TYPE
                          The type of kaldi data type to read. Defaults to base matrix
    -o OUT_TYPE, --out-type OUT_TYPE
                          The numpy data type to cast values to. The default is dependent on the input type. String types will be written as (tuples of) strings

write-pickle-to-table
---------------------

::

  write-pickle-to-table -h
  usage: write-pickle-to-table [-h] [-v VERBOSE] [--config CONFIG] [--print-args PRINT_ARGS] [-o OUT_TYPE] value_in [key_in] wspecifier
  
  Write pickle file(s) contents to a table
  
      The inverse is write-table-to-pickle
      
  
  positional arguments:
    value_in              A path to read (key,value) pairs from, or just values if key_in was set. If it ends in ".gz", the file is assumed to be gzipped
    key_in                A path to read keys from. If it ends in ".gz", the file is assumed to be gzipped
    wspecifier            The table to write to
  
  optional arguments:
    -h, --help            show this help message and exit
    -v VERBOSE, --verbose VERBOSE
                          Verbose level (higher->more logging)
    --config CONFIG
    --print-args PRINT_ARGS
    -o OUT_TYPE, --out-type OUT_TYPE
                          The type of kaldi data type to read. Defaults to base matrix

compute-error-rate
------------------

::

  compute-error-rate -h
  usage: compute-error-rate [-h] [-v VERBOSE] [--config CONFIG] [--print-args PRINT_ARGS] [--print-tables PRINT_TABLES] [--strict STRICT] [--insertion-cost INSERTION_COST]
                            [--deletion-cost DELETION_COST] [--substitution-cost SUBSTITUTION_COST] [--include-inserts-in-cost INCLUDE_INSERTS_IN_COST]
                            [--report-accuracy REPORT_ACCURACY]
                            ref_rspecifier hyp_rspecifier [out_path]
  
  Compute error rates between reference and hypothesis token vectors
  
      Two common error rates in speech are the word (WER) and phone (PER), though the
      computation is the same. Given a reference and hypothesis sequence, the error rate
      is
  
          error_rate = (substitutions + insertions + deletions) / (ref_tokens * 100)
  
      Where the number of substitutions (e.g. "A B C -> A D C"), deletions (e.g. "A B C ->
      A C"), and insertions (e.g. "A B C -> A D B C") are determined by Levenshtein
      distance.
      
  
  positional arguments:
    ref_rspecifier        Rspecifier pointing to reference (gold standard) transcriptions
    hyp_rspecifier        Rspecifier pointing to hypothesis transcriptions
    out_path              Path to print results to. Default is stdout.
  
  optional arguments:
    -h, --help            show this help message and exit
    -v VERBOSE, --verbose VERBOSE
                          Verbose level (higher->more logging)
    --config CONFIG
    --print-args PRINT_ARGS
    --print-tables PRINT_TABLES
                          If set, will print breakdown of insertions, deletions, and subs to out_path
    --strict STRICT       If set, missing utterances will cause an error
    --insertion-cost INSERTION_COST
                          Cost (in terms of edit distance) to perform an insertion
    --deletion-cost DELETION_COST
                          Cost (in terms of edit distance) to perform a deletion
    --substitution-cost SUBSTITUTION_COST
                          Cost (in terms of edit distance) to perform a substitution
    --include-inserts-in-cost INCLUDE_INSERTS_IN_COST
                          Whether to include insertions in error rate calculations
    --report-accuracy REPORT_ACCURACY
                          Whether to report accuracy (1 - error_rate) instead of the error rate

normalize-feat-lens
-------------------

::

  normalize-feat-lens -h
  usage: normalize-feat-lens [-h] [-v VERBOSE] [--config CONFIG] [--print-args PRINT_ARGS] [--type TYPE] [--tolerance TOLERANCE] [--strict STRICT]
                             [--pad-mode {zero,constant,edge,symmetric,mean}] [--side {left,right,center}]
                             feats_in_rspecifier len_in_rspecifier feats_out_wspecifier
  
  Ensure features match some reference lengths
  
      Incoming features are either clipped or padded to match reference lengths (stored as
      an int32 table), if they are within tolerance.
      
  
  positional arguments:
    feats_in_rspecifier   The features to be normalized
    len_in_rspecifier     The reference lengths (int32 table)
    feats_out_wspecifier  The output features
  
  optional arguments:
    -h, --help            show this help message and exit
    -v VERBOSE, --verbose VERBOSE
                          Verbose level (higher->more logging)
    --config CONFIG
    --print-args PRINT_ARGS
    --type TYPE           The kaldi type of the input/output features
    --tolerance TOLERANCE
                          How many frames deviation from reference to tolerate before error. The default is to be infinitely tolerant (a feat I'm sure we all desire)
    --strict STRICT       Whether missing keys in len_in and lengths beyond the threshold cause an error (true) or are skipped with a warning (false)
    --pad-mode {zero,constant,edge,symmetric,mean}
                          If frames are being padded to the features, specify how they should be padded. zero=zero pad, edge=pad with rightmost frame, symmetric=pad with
                          reverse of frame edges, mean=pad with mean feature values
    --side {left,right,center}
                          If an utterance needs to be padded or truncated, specify what side of the utterance to do this on. left=beginning, right=end, center=distribute
                          evenly on either side

write-table-to-torch-dir
------------------------

::

  write-table-to-torch-dir -h
  usage: write-table-to-torch-dir [-h] [-v VERBOSE] [--config CONFIG] [--print-args PRINT_ARGS] [-i IN_TYPE] [-o {float,double,half,byte,char,short,int,long}]
                                  [--file-prefix FILE_PREFIX] [--file-suffix FILE_SUFFIX]
                                  rspecifier dir
  
  Write a Kaldi table to a series of PyTorch data files in a directory
  
      Writes to a folder in the format:
      
          folder/
              <file_prefix><key_1><file_suffix>
              <file_prefix><key_2><file_suffix>
              ...
  
      The contents of the file "<file_prefix><key_1><file_suffix>" will be a PyTorch
      tensor corresponding to the entry in the table for "<key_1>"
      
  
  positional arguments:
    rspecifier            The table to read
    dir                   The folder to write files to
  
  optional arguments:
    -h, --help            show this help message and exit
    -v VERBOSE, --verbose VERBOSE
                          Verbose level (higher->more logging)
    --config CONFIG
    --print-args PRINT_ARGS
    -i IN_TYPE, --in-type IN_TYPE
                          The type of table to read
    -o {float,double,half,byte,char,short,int,long}, --out-type {float,double,half,byte,char,short,int,long}
                          The type of torch tensor to write. If unset, it is inferrred from the input type
    --file-prefix FILE_PREFIX
                          The file prefix indicating a torch data file
    --file-suffix FILE_SUFFIX
                          The file suffix indicating a torch data file

write-torch-dir-to-table
------------------------

::

  write-torch-dir-to-table -h
  usage: write-torch-dir-to-table [-h] [-v VERBOSE] [--config CONFIG] [--print-args PRINT_ARGS] [-o OUT_TYPE] [--file-prefix FILE_PREFIX] [--file-suffix FILE_SUFFIX]
                                  dir wspecifier
  
  Write a data directory containing PyTorch data files to a Kaldi table
  
      Reads from a folder in the format:
  
          folder/
            <file_prefix><key_1><file_suffix>
            <file_prefix><key_2><file_suffix>
            ...
  
      Where each file contains a PyTorch tensor. The contents of the file
      "<file_prefix><key_1><file_suffix>" will be written as a value in a Kaldi table with
      key "<key_1>"
      
  
  positional arguments:
    dir                   The folder to read files from
    wspecifier            The table to write to
  
  optional arguments:
    -h, --help            show this help message and exit
    -v VERBOSE, --verbose VERBOSE
                          Verbose level (higher->more logging)
    --config CONFIG
    --print-args PRINT_ARGS
    -o OUT_TYPE, --out-type OUT_TYPE
                          The type of table to write to
    --file-prefix FILE_PREFIX
                          The file prefix indicating a torch data file
    --file-suffix FILE_SUFFIX
                          The file suffix indicating a torch data file

