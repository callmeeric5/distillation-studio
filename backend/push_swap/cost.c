
#include "push_swap.h"

static void	update_best(t_move *m, int total, int cost_a, int cost_b)
{
	if (total < m->total)
	{
		m->total = total;
		m->cost_a = cost_a;
		m->cost_b = cost_b;
	}
}

static void	eval_moves(t_move *m, int ra_steps, int rb_steps, t_sizes sizes)
{
	int	rra_steps;
	int	rrb_steps;
	int	total;

	rra_steps = sizes.a - ra_steps;
	rrb_steps = sizes.b - rb_steps;
	total = ra_steps;
	if (rb_steps > total)
		total = rb_steps;
	update_best(m, total, ra_steps, rb_steps);
	total = rra_steps;
	if (rrb_steps > total)
		total = rrb_steps;
	update_best(m, total, -rra_steps, -rrb_steps);
	update_best(m, ra_steps + rrb_steps, ra_steps, -rrb_steps);
	update_best(m, rra_steps + rb_steps, -rra_steps, rb_steps);
}

t_move	best_move(t_stack *a, t_stack *b)
{
	t_move	best_move;
	t_stack	*node;

	best_move.total = INT_MAX;
	best_move.target = NULL;
	node = b;
	while (node)
	{
		calc_move(&best_move, a, b, node);
		node = node->next;
	}
	return (best_move);
}

void	calc_move(t_move *m, t_stack *a, t_stack *b, t_stack *node)
{
	int		a_pos;
	int		b_pos;
	t_sizes	sizes;

	a_pos = get_target_pos(a, node->index);
	b_pos = pos_in_stack(b, node);
	sizes.a = get_stack_size(a);
	sizes.b = get_stack_size(b);
	m->target = node;
	eval_moves(m, a_pos, b_pos, sizes);
}
