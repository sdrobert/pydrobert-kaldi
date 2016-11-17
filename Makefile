.PHONY: clean all kaldi_cxxflags kaldi_ldlibs kaldi_ldflags
all: kaldi_cxxflags kaldi_ldlibs kaldi_ldflags

include $(KALDI_ROOT)/src/kaldi.mk

kaldi_cxxflags:
	echo $(CXXFLAGS) > $@

kaldi_ldlibs:
	echo $(LDLIBS) > $@

kaldi_ldflags:
	echo $(LDFLAGS) > $@

FORCE:

clean:
	rm -f kaldi_cxxflags kaldi_ldflags kaldi_ldlibs
