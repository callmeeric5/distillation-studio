FILES = ops_a_b ops_a ops_b ops_base quick_sort stack_utils utils bench parser validator tiny_sort core_sort medium_sort align cost move rotate medium_sort_utils_1 medium_sort_utils_2
COMMON_SRC = $(addsuffix .c, $(FILES))
SRC = $(COMMON_SRC) main.c
OBJ = $(SRC:%.c=%.o)
DEP = $(SRC:%.c=%.d)
NAME = push_swap
COMMON_OBJ = $(COMMON_SRC:%.c=%.o)
CC = cc
CFLAGS = -Wall -Werror -Wextra -I . -MMD -MP
RM = rm -f
all: $(NAME)
$(NAME): $(OBJ)
	$(CC) $(CFLAGS) $(OBJ) -o $(NAME)
%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@
clean:
	$(RM) $(OBJ) $(DEP)
fclean: clean
	$(RM) $(NAME)
re: fclean all
-include $(DEP)
.PHONY: all clean fclean re
