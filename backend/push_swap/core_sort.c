
#include "push_swap.h"

void	simple_sort(t_stack **a, t_stack **b, t_bench *bench, int size)
{
	tiny_sort(a, b, bench, size);
	while (*b)
	{
		pa(b, a, bench);
	}
}

void	complex_sort(t_stack **a, t_stack **b, t_bench *bench, int size)
{
	int	processed;
	int	last_idx;

	processed = 0;
	last_idx = -1;
	while (processed < size)
	{
		if ((*a)->index > last_idx)
		{
			last_idx = (*a)->index;
			ra(a, bench);
		}
		else
			pb(a, b, bench);
		processed++;
	}
	move_to_a(a, b, bench);
	final_align(a, bench);
}

void	medium_sort(t_stack **a, t_stack **b, t_bench *bench)
{
	int	*tb;
	int	nb_of_chunks;
	int	i;

	nb_of_chunks = 5;
	if (get_stack_size(*a) > 100)
		nb_of_chunks = 11;
	tb = set_chunks(a, nb_of_chunks);
	if (!tb)
		display_stack_error(a);
	i = 0;
	while (i < nb_of_chunks)
	{
		push_chunk_to_b(a, b, tb[i], bench);
		i++;
	}
	push_all_b_to_a(a, b, bench);
	free(tb);
}

void	adaptive_sort(t_stack **a, t_stack **b, t_bench *bench, int size)
{
	if (bench->disorder < 0.2)
		simple_sort(a, b, bench, size);
	else if (bench->disorder < 0.5)
		medium_sort(a, b, bench);
	else
		complex_sort(a, b, bench, size);
}

void	run_sort(t_stack **a, t_stack **b, t_bench *bench, t_config *config)
{
	int	size;

	size = get_stack_size(*a);
	if (size <= 1)
		return ;
	if (size == 2)
	{
		sort_two(a, bench);
		return ;
	}
	if (size <= 5)
	{
		tiny_sort(a, b, bench, size);
		while (*b)
			pa(b, a, bench);
		return ;
	}
	if (config->algo == SIMPLE)
		simple_sort(a, b, bench, size);
	else if (config->algo == MEDIUM)
		medium_sort(a, b, bench);
	else if (config->algo == COMPLEX)
		complex_sort(a, b, bench, size);
	else
		adaptive_sort(a, b, bench, size);
}
