
#include "push_swap.h"

static int	is_in_chunk(t_stack *node, int min, int max)
{
	return (node->val >= min && node->val <= max);
}

static int	find_top_chunk_pos(t_stack *stack, int min, int max)
{
	int	pos;

	pos = 0;
	while (stack)
	{
		if (is_in_chunk(stack, min, max))
			return (pos);
		pos++;
		stack = stack->next;
	}
	return (-1);
}

static int	find_bottom_chunk_pos(t_stack *stack, int min, int max)
{
	int	size;
	int	pos;

	size = get_stack_size(stack);
	pos = size - 1;
	stack = last_node(stack);
	while (stack)
	{
		if (is_in_chunk(stack, min, max))
			return (pos);
		pos--;
		stack = stack->prev;
	}
	return (-1);
}

static void	rotate_a_to_pos(t_stack **a, int pos, t_bench *bench)
{
	size_t	size_a;
	int		moves;
	int		i;

	size_a = get_stack_size(*a);
	if (pos > (int)size_a / 2)
	{
		moves = size_a - pos;
		while (moves--)
			rra(a, bench);
	}
	else
	{
		i = 0;
		while (i++ < pos)
			ra(a, bench);
	}
}

static void	rotate_b_to_pos(t_stack **b, int pos, t_bench *bench)
{
	int	size_b;
	int	moves;

	size_b = get_stack_size(*b);
	if (pos > size_b / 2)
	{
		moves = size_b - pos;
		while (moves--)
			rrb(b, bench);
	}
	else
	{
		moves = 0;
		while (moves++ < pos)
			rb(b, bench);
	}
}

static void	move_chunk_candidate_to_top(t_stack **a, int min, int max,
		t_bench *bench)
{
	int	top_pos;
	int	bottom_pos;
	int	size_a;
	int	target_pos;

	top_pos = find_top_chunk_pos(*a, min, max);
	bottom_pos = find_bottom_chunk_pos(*a, min, max);
	size_a = get_stack_size(*a);
	if (bottom_pos != -1 && size_a - bottom_pos < top_pos)
		target_pos = bottom_pos;
	else
		target_pos = top_pos;
	rotate_a_to_pos(a, target_pos, bench);
}

static void	prepare_b_for_push(t_stack **a, t_stack **b, t_bench *bench)
{
	t_stack	*tmp;
	int		pos_target;

	tmp = *b;
	if (tmp)
	{
		if ((*a)->val > get_max_val_stack(tmp)
			|| (*a)->val < get_min_val_stack(tmp))
			pos_target = get_val_pos_stack(tmp, get_min_val_stack(tmp));
		else
			pos_target = find_target_in_b(*b, (*a)->val);
		rotate_b_to_pos(b, pos_target, bench);
	}
}

void	push_chunk_to_b(t_stack **a, t_stack **b, int max,
		t_bench *bench)
{
	int	min;

	min = get_min_val_stack(*a);
	while (find_top_chunk_pos(*a, min, max) != -1)
	{
		move_chunk_candidate_to_top(a, min, max, bench);
		prepare_b_for_push(a, b, bench);
		pb(a, b, bench);
	}
}

void	push_all_b_to_a(t_stack **a, t_stack **b, t_bench *bench)
{
	int		pos_val_max;

	while (*b)
	{
		pos_val_max = get_val_pos_stack(*b, get_max_val_stack(*b));
		rotate_b_to_pos(b, pos_val_max, bench);
		pa(b, a, bench);
	}
}
