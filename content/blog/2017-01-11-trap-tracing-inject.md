Title: Trapflag-Tracing II:</br>Injecting Trapflag-Tracing into Compiled Programs
Slug: trap-tracing-inject
Date: 2017-02-23 18:00:00
status: published

*This post continues the exploration of using the x86 trap flag
 and signal handlers to observe the execution of a program; this time
 with the goal of injecting the 'debugger' into a compiled binary.
 This includes an overview of LD_PRELOAD.*


In my [last post]({filename}/blog/2017-01-11-trapflag-tracing.md)
I introduced the idea of observing every step of
the execution of a program by setting the x86 trap flag which causes
an interrupt after every instruction, and a signal handler to catch
that interrupt within the same process. This turns out to be much
faster than using the Linux `ptrace` facilty, which is the 'proper'
way to write a debugger to observe the execution of a program.

The flow looks kind of like this:

<img style="width: 80%; display:block; margin-left:auto; margin-right: auto" src="{filename}/images/trap-trace/traptrace-flow.jpg">

One issue is that as a 'debugger' this is not very useful if code has
to be inserted into the source of the program that you want to
observe. It would be much more useful if we could inject this into an
already compiled program.

The easiest way to inject code into a compiled program is to use
`LD_PRELOAD`.  This is an environment variable that allows overriding
dynamic library functions that a program uses.

Aside: LD_PRELOAD explained
===========================

Every time a program is loaded to be executed, there's a program
called the dynamic linker that, among other things, finds the list of
dynamic library functions that the program uses, and links them into
the executable (dynamic libraries are `.so` files).

When the `LD_PRELOAD` environment variable refers to the
filename of a dynamic library, the dynamic linker will attempt to
always find a dynamic function in that library first. Thus it allows
us to override dynamic functions.

Julia Evans explains this well in
[this post](https://jvns.ca/blog/2014/11/27/ld-preload-is-super-fun-and-easy/),
which in turn refers to the nice tutorial
[Dynamic linker tricks: Using LD_PRELOAD to cheat, inject features and investigate programs](https://rafalcieslak.wordpress.com/2013/04/02/dynamic-linker-tricks-using-ld_preload-to-cheat-inject-features-and-investigate-programs/)
by Rafał Cieślak.

Let's do a simple hello world example program that we will override:

```
#include <stdio.h>

int main() {
    printf("hello\n");
    printf("world!\n");
}
```

We can figure out which dynamic functions are called using `nm -D`:

```
>> nm -D hello
  w __gmon_start__
  080484cc R _IO_stdin_used
  U __libc_start_main
  U puts
```

Apparently the program uses `puts` to write the output on screen.
We can write a tiny shared library to override it:

```
#include <unistd.h>

int puts(const char *str) {
    write(1, "NOPE!\n", 6);
    return 1; // success
}
```

Note that we can't use `puts` itself when printing, because this
will result in the function calling itself. We'll just use
the write system call to output on screen.

We need some special way to compile the function to create a shared
library:
```
>> gcc -shared -fPIC override.c -o override.so
```
And then we can use `LD_PRELOAD` and override `puts` in our hello-world
example:
```
>> LD_PRELOAD=./override.so ./hello
  NOPE!
  NOPE!
```
We may have a problem if we need to call the original function that
was overridden. Thankfully, we ask the dynamic loader to give us a pointer
to the original function using `dlsym`:

```
#define_GNU_SOURCE
#include <dlfcn.h>
#include <stdlib.h>

typedef int (*putsfn)(const char* str);

int puts(const char *str) {
    static putsfn orig_puts = NULL;
    if (orig_puts == NULL)
        orig_puts = (putsfn)dlsym(RTLD_NEXT, "puts"); // get original puts
    return original_puts("NOPE!");
}
```

To compile, we now need to tell gcc to include `libdl` via `-ldl`.

Using LD_PRELOAD to inject trap-flag tracing
============================================

Back to our problem at hand -- how are going to inject trap-flag
tracing into an already compiled program? The trivial program I was
using in the [last post]()({filename}/blog/2017-01-11-trapflag-tracing.md)
was one that merely executes a million
instructions and then quits.

```c
void main() {
  int num_instructions = 1000000;
  unsigned int count = num_instructions >> 1;
  asm volatile(
      "1:\n" // define local label
      "decl %%eax\n" // eax -= 1
      "jnz 1b\n" // jump to previous local label 1 (before) if not zero
      : // no output regs
      : "a"(count) // input count -> eax
      );
}
```

If we want to use `LD_PRELOAD` to inject the tracer, we have to find
some dynamic library function this program is calling. And it should
be as early in the program as possible, and should be ideally called
by any program. In our example program we don't make any explicit
library calls, but may there's still some setup code? Let's just check what
the program uses using `nm -D`:

```
>> nm -D loop
           w __gmon_start__
  0804847c R _IO_stdin_used
           U __libc_start_main
```

This `__libc_start_main` function seems like an interesting candidate!

Some poking around the [source code of libc](http://ftp.gnu.org/gnu/libc/)
(find your version using `ldd --version`) revealed that this is
actually the function that calls `main`! So this function
will start executing even before `main`.

This means we could intercept `__libc_start_main`, start the tracer by
setting the trap-signal handler and setting the trap flag. Then we can
call the original `__libc_start_main` to start the original
program. This should allow us to inject the trap-flag tracer into
arbitrary compiled programs, as long as they are based on `libc` (and
call `libc` dynamically, i.e. they are not statically compiled).

Our overridden `__lib_start_main` looks like this:

```c
// declare type of __libc_start_main function
typedef int (*MainFnType)(int (*main)(int, char **, char **),
                          int argc,
                          char **argv,
                          int (*init)(void),
                          void (*fini)(void),
                          void (*ldso_fini)(void),
                          void (*stack_end));

// override __libc_start_main
int __libc_start_main(int (*main)(int, char **, char **),
                      int argc,
                      char **argv,
                      int (*init)(void),
                      void (*fini)(void),
                      void (*ldso_fini)(void),
                      void (*stack_end)) {
  // get original function
  MainFnType orig_main = (MainFnType)dlsym(RTLD_NEXT,
                                           "__libc_start_main");
  
  // start tracing
  startTrace();
  
  // call original function
  int result = orig_main(main, argc, argv,
                         init, fini, ldso_fini, stack_end);
  return result;
}
```

The start/stop trace functions are the same as for the previous
post:

```c
static struct sigaction trapSa;
void startTrace() {
  // set up trap signal handler
  trapSa.sa_flags = SA_SIGINFO;
  trapSa.sa_sigaction = trapHandler;
  sigaction(SIGTRAP, &trapSa, NULL);
    
  setTrapFlag();
}

void stopTrace() {
  clearTrapFlag();
  printf("cycles: %lld\n", ccycle);
}

void setTrapFlag() {
  asm volatile("pushfl\n" // push status register to stack
               "orl $0x100, (%esp)\n" // set trap-flag of on-stack value 
               "popfl\n" // pop status register
               );
}

void clearTrapFlag() {
  asm volatile("pushfl\n" // push status register
               "andl $0xfffffeff, (%esp)\n" // clear trap-flag
               "popfl\n" // pop status register
               );
}
```

In the actual code, I added some trickery catching the exit
system call in order to find when the program finishes. I'll
explain how this works in the next post. For now let's just
assume we can catch the exit of the program, and execute
the an exit handler. Again we will only count the cycles,
and print how many cycles executed at the end of the program.

Now, if we run this on our trivial loop example, we get this:

```
>> LD_PRELOAD=./override.so loop
  intercepted sys exit. cycles:0x000f499c
```

And it works!

Now we can trace compiled programs.
Let's try tracing some other simple programs:

```
>> LD_PRELOAD=./override.so /bin/echo hello world
  hello world
  /bin/echo: write error
  intercepted sys exit. cycles:0x0003a70c

>> LD_PRELOAD=./override.so /bin/ls
  LICENSE  override.c   README.md  tracer.h
  make.sh  override.so  tracer.c
  /bin/ls: write error
  intercepted sys exit. cycles:0x0003878f
```

(Note that we're explicitly calling the programs, because `echo`
by itself may be dealt with directly by the shell)

This defintely works, although I'd prefer not to have those
write errors.

But overall, now we have a way to step through an arbitrary compiled
program, assuming that is based on the `libc` library. At a next step,
we can figure out how exactly I intercepted those exits, and actually
collect some useful information about the execution of the program.

*See the [source code at the current
 commit](https://github.com/ant6n/traptrace/tree/b120f054c666d51ef9049513932bd36c8b853fbf)
 on github.*


