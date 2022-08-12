Locale and Kaldi
================

After ``v0.6.0``, ``pydrobert.kaldi.io`` no longer issues a
``KaldiLocaleWarning`` when the system locale doesn't match the POSIX standard.
*The long story short is that locale shouldn't matter much to what
pydrobert-kaldi does,* so I no longer bug you about it. If you're hunting an
error, however, read on.

Most Kaldi shell scripts presume 

.. code-block:: shell

  export LC_ALL=C

has been called some time prior to running the current script. This sets the
locale to POSIX-style, which is going to ensure your various shell commands
sort stuff like C does. The Kaldi codebase is written in C, so it's definitely
going to sort this way. Here's an example of some weirdness involving the
``"s"`` flag in the file rxspecifier. It basically tells Kaldi that table
entries are in sorted order, which allows Kaldi to take some shortcuts to save
on read/write costs.

.. code-block:: shell

  # I've previously installed the German and Russian locales on Ubuntu:
  # sudo locale-gen de_DE
  # sudo locale-gen ru_RU

  export LC_ALL=C

  python -c "print('f\xe4n a'); print('foo b')" | \
    sort | \
    python -c "
  from pydrobert.kaldi.io import open as kopen
  with kopen('ark,s:-', 't', 'r+') as f:
      print(f['foo'])
  "
  # outputs: b
  # sort sorts C-style ("foo" first), kaldi sorts C-style

  python -c "print('f\xe4n a'); print('foo b')" | \
    LC_ALL=de_DE sort | \
    python -c "
  from pydrobert.kaldi.io import open as kopen
  with kopen('ark,s:-', 't', 'r+') as f:
      print(f['foo'])
  "
  # KeyError: 'foo'
  # sort sorts German ("fän" first), kaldi sorts C-style

  python -c "print('f\xe4n a'); print('foo b')" | \
    sort | \
    LC_ALL=de_DE python -c "
  from pydrobert.kaldi.io import open as kopen
  with kopen('ark,s:-', 't', 'r+') as f:
      print(f['foo'])
  "
  # outputs: b
  # sort sorts C-style, kaldi ignores German encoding and sorts C-style

These examples will lead to exceptions which can be caught and debugged. One
can come up with more insidious errors which don't fail, mind you.

For the most part, however, this is a non-issue, at least for
`pydrobert-kaldi`. The only situation the library might mess up in that I know
of involves sorting table keys, and the table keys are (as far as I can tell)
exclusively ASCII. Also as far as I can tell, even locales which contain
characters visually identical to those in the Latin alphabet are nonetheless
encoded outside of the ASCII range. For example:

.. code-block:: shell

  export LC_ALL=C
  echo $'M\nC' | LC_ALL=ru_RU sort
  # outputs: C, M
  # these are the ASCII characters
  echo $'М\nС' | LC_ALL=ru_RU sort  
  # outputs: M, C
  # these are UTF characters 'U+0421' and 'U+0043', respectively

Besides UTF, ISO-8859-1 maintains a contiguous ASCII range. Technically there's
no guarantee that this will be the case for all encodings, though any such
encoding would probably break all sorts of legacy code. If you have a
counterexample of a Kaldi recipe that does otherwise, please let me know and
I'll mention it here.

Other than that, the library is quite agnostic to locale. An error involving
locales is, more likely than not, something that occurred before or after the
library was called.
