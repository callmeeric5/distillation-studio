
#include "push_swap.h"

int	get_target_pos(t_stack *a, int b_idx)
{
	int		best_idx;
	int		best_pos;
	int		i;
	t_stack	*cur;

	best_idx = INT_MAX;
	best_pos = 0;
	i = 0;
	cur = a;
	while (cur)
	{
		if (cur->index > b_idx && cur->index < best_idx)
		{
			best_idx = cur->index;
			best_pos = i;
		}
		cur = cur->next;
		i++;
	}
	if (best_idx != INT_MAX)
		return (best_pos);
	return (get_min_pos(a));
}

int	pos_in_stack(t_stack *stack, t_stack *node)
{
	int	pos;

	pos = 0;
	while (stack && stack != node)
	{
		stack = stack->next;
		pos++;
	}
	return (pos);
}

void	final_align(t_stack **a, t_bench *bench)
{
	int	pos;
	int	size;
	int	steps;

	pos = get_min_pos(*a);
	size = get_stack_size(*a);
	if (pos <= size / 2)
		steps = pos;
	else
		steps = pos - size;
	rotate_steps(a, &steps, bench, (t_rot_fns){ra, rra});
}
