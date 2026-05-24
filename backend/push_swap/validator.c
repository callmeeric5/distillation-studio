
#include "push_swap.h"

static int	is_space(int c)
{
	if ((c >= 9 && c <= 13) || c == 32)
		return (1);
	return (0);
}

static int	is_duplicate(t_stack *stack, int val)
{
	while (stack)
	{
		if (val == stack->val)
			return (1);
		stack = stack->next;
	}
	return (0);
}

static void	validate_segment(char *seg, t_stack **stack)
{
	int	val;

	if (!seg)
		display_stack_error(stack);
	while (is_space(*seg))
		seg++;
	if (*seg == '\0')
		display_stack_error(stack);
	while (*seg)
	{
		val = extract_number(&seg, stack);
		if (is_duplicate(*stack, val))
			display_stack_error(stack);
		if (*seg && !is_space(*seg))
			display_stack_error(stack);
		push_stack(stack, val);
		while (is_space(*seg))
			seg++;
	}
}

void	validate(char **argv, t_stack **stack, t_config *config)
{
	int			i;
	t_algo_type	algo;

	i = 1;
	while (argv[i] && argv[i][0] == '-' && argv[i][1] == '-')
	{
		if (ft_strcmp(argv[i], "--bench") == 0)
			config->mode = 1;
		else
		{
			algo = extract_strategy(argv[i]);
			if (algo == NONE)
				display_stack_error(stack);
			if (config->algo != ADAPTIVE)
				display_stack_error(stack);
			config->algo = algo;
		}
		i++;
	}
	while (argv[i])
	{
		validate_segment(argv[i], stack);
		i++;
	}
}
