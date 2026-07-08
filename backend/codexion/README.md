*This activity has been created as part of the 42 curriculum by <login>.*

# Codexion

## Description

Codexion is a C concurrency simulation inspired by shared development
resources. Several coders sit around a table and need two USB dongles to
compile. After compiling, they debug, refactor, and then try to compile again.

The goal is to coordinate all coder threads so that dongles are shared safely,
cooldowns are respected, logs stay readable, and the simulation stops when a
coder burns out or when every coder has compiled enough times.

## Instructions

Compile the project with:

```sh
make
```

Run it with all required arguments:

```sh
./codexion number_of_coders time_to_burnout time_to_compile time_to_debug time_to_refactor number_of_compiles_required dongle_cooldown scheduler
```

The scheduler must be exactly `fifo` or `edf`.

Example:

```sh
./codexion 4 800 200 200 200 3 0 fifo
```

Useful Makefile rules:

```sh
make clean
make fclean
make re
```

## Blocking cases handled

The implementation avoids deadlock by granting both dongles atomically. A coder
does not keep one dongle while waiting for the second one, which removes the
circular wait condition.

Starvation is reduced through per-dongle priority queues. With `fifo`, requests
are served in arrival order. With `edf`, the request with the earliest burnout
deadline is preferred, with deterministic tie-breakers.

Dongle cooldown is handled after every release. A released dongle cannot be
granted again until its cooldown timestamp has passed.

Burnout is detected by a separate monitor thread that checks coder deadlines and
stops the simulation as soon as a missed deadline is found.

Logs are serialized so messages from different threads do not interleave on the
same line.

## Thread synchronization mechanisms

Each coder is represented by one `pthread_t`. The monitor also runs in its own
thread.

Shared simulation state is protected by a `pthread_mutex_t`. This mutex protects
dongle state, priority queues, compile counters, stop state, and coder deadlines.

Each coder owns a `pthread_cond_t`. A coder waits on this condition while its
request is queued. When dongles are released or the simulation stops, all coders
are woken so they can re-check the shared state.

Logging is protected by a dedicated mutex, so a complete state message is printed
before another thread can print its own message.

The priority queue is a small custom binary heap. It stores pending dongle
requests and orders them by FIFO sequence or EDF deadline depending on the
selected scheduler.

## Resources

- `pthread_create`, `pthread_join`, `pthread_mutex_t`, and `pthread_cond_t`
  manual pages.
- `gettimeofday` manual page for millisecond timing.
- The 42 Codexion subject PDF.
- AI was used to help plan and draft this implementation, especially the project
  structure, concurrency design, and README wording. The code should still be
  reviewed and tested carefully before evaluation.
