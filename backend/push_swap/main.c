
#include "push_swap.h"

int	main(int argc, char **argv)
{
	t_config	config;
	t_stack		*a;
	t_stack		*b;
	t_bench		bench;

	config.algo = ADAPTIVE;
	config.mode = 0;
	a = NULL;
	b = NULL;
	if (argc < 2)
		return (0);
	validate(argv, &a, &config);
	init_bench(&bench, a, config.mode);
	init_stack_idx(&a);
	if (!is_sorted_stack(a))
		run_sort(&a, &b, &bench, &config);
	if (config.mode == 1)
		write_bench(&bench, &config);
	clear_stack(&a);
	clear_stack(&b);
	return (0);
}
