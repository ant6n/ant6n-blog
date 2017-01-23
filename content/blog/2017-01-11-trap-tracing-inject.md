Title: Trapflag-Tracing II: Injecting Trapflag-Tracing into Compiled Programs
Slug: 2017-01-11-trap-tracing-inject
Date: 2017-01-11 19:37:49

*This post continues the exploration of using the x86 trap flag
 and signal handlers to observe the execution of a program; this time
 with the goal of injecting the 'debugger' into a compiled binary.
 This includes an overview of LD_PRELOAD.*


In my [last post]() I introduced the idea of observing every step of
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
Let's override it to print something else.

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

Back to our problem at hand -- how are going to inject trap-flag tracing
into an already compiled program. The trivial program I was using
last time was one that merely executes a million instructions and
then quits.

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
some dynamic library function this program is calling. And it should be
as early in the program as possible. In the program we don't make any
explicit calls, but may there's some setup code? Let's just check what
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
actually the function that calls the `main`. So this function
will start executing even before `main`.

This means we could intercept `__libc_start_main`, start the tracer by
setting the trap-signal handler and setting the trap flag. Then we can
call the original `__libc_start_main` to start the original
program. This should allow us to inject the trap-flag tracer into
arbitrary compiled programs, as long as they are based on `libc` (and
call `libc` dynamically, i.e. they are not statically compiled).

Our overridden `__lib_start_main` looks like this:

```c

```

The start/stop trace functions are the same as for the previous
post:

```c

```

We'll use a simple bash script to run the trap-tracer:

```sh

```

Now, if we run this on our trivial loop example, we get this:

```

```

And it works!

Now we can trace compiled programs.
Let's try tracing some other simple programs:

```
/bin/echo

/bin/ls

```

(Note that we're explicitly calling the programs, because `echo`
by itself may be dealt with directly by the shell)

So now we have a way to step through an arbitrary compiled program,
assuming that is based on the `libc` library. At a next step, we can
try to collect some more useful information about programs.


