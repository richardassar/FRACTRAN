# Build the native FRACTRAN core. GMP is taken from the active conda env by
# default; override GMP_PREFIX to point elsewhere.
CXX ?= g++
GMP_PREFIX ?= $(HOME)/miniforge3/envs/sage

CXXFLAGS = -O2 -std=c++17 -Wall -I$(GMP_PREFIX)/include
LDFLAGS  = -L$(GMP_PREFIX)/lib -Wl,-rpath,$(GMP_PREFIX)/lib -lgmpxx -lgmp

fractran_core: fractran_core.cpp
	$(CXX) $(CXXFLAGS) -o $@ $< $(LDFLAGS)

clean:
	rm -f fractran_core

.PHONY: clean
