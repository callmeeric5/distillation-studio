
#include "push_swap.h"

void	move_to_a(t_stack **a, t_stack **b, t_bench *bench)
{
	t_move	m;

	while (*b)
	{
		m = best_move(*a, *b);
		apply_move(a, b, &m, bench);
	}
}

void	apply_move(t_stack **a, t_stack **b, t_move *m, t_bench *bench)
{
	t_rot_fns	fns;

	rotate_both(a, b, m, bench);
	fns.up = ra;
	fns.down = rra;
	rotate_steps(a, &m->cost_a, bench, fns);
	fns.up = rb;
	fns.down = rrb;
	rotate_steps(b, &m->cost_b, bench, fns);
	pa(b, a, bench);
}
