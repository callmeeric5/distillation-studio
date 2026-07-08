NAME = codexion

CC = cc
CFLAGS = -Wall -Wextra -Werror -pthread
INCLUDES = -Iinclude

SRCS = src/main.c \
	src/parse.c \
	src/heap.c \
	src/heap_order.c \
	src/heap_query.c \
	src/sim_init.c \
	src/sim_release.c \
	src/sim_request.c \
	src/sim_run.c \
	src/sim_state.c \
	src/sim_threads.c \
	src/time.c

OBJS = $(SRCS:.c=.o)

all: $(NAME)

$(NAME): $(OBJS)
	$(CC) $(CFLAGS) $(OBJS) -o $(NAME)

%.o: %.c include/codexion.h
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

clean:
	rm -f $(OBJS)

fclean: clean
	rm -f $(NAME)

re: fclean all

.PHONY: all clean fclean re
