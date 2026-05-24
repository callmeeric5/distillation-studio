
#include "push_swap.h"

void	rotate_both(t_stack **a, t_stack **b, t_move *m, t_bench *bench)
{
	while (m->cost_a > 0 && m->cost_b > 0)
	{
		rr(a, b, bench);
		m->cost_a--;
		m->cost_b--;
	}
	while (m->cost_a < 0 && m->cost_b < 0)
	{
		rrr(a, b, bench);
		m->cost_a++;
		m->cost_b++;
	}
}

void	rotate_steps(t_stack **stack, int *steps, t_bench *bench, t_rot_fns fns)
{
	while (*steps > 0)
	{
		fns.up(stack, bench);
		(*steps)--;
	}
	while (*steps < 0)
	{
		fns.down(stack, bench);
		(*steps)++;
	}
}
