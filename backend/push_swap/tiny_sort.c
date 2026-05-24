
#include "push_swap.h"

int	get_min_pos(t_stack *stack)
{
	int	pos;
	int	min_pos;
	int	min;

	pos = 0;
	min_pos = 0;
	min = stack->val;
	while (stack)
	{
		if (stack->val < min)
		{
			min = stack->val;
			min_pos = pos;
		}
		pos++;
		stack = stack->next;
	}
	return (min_pos);
}

void	sort_two(t_stack **a, t_bench *bench)
{
	if ((*a)->val > (*a)->next->val)
		sa(a, bench);
}

static void	sort_stack_3(t_stack **a, t_bench *bench)
{
	int	first;
	int	second;
	int	third;

	if (is_sorted_stack(*a))
		return ;
	first = (*a)->val;
	second = (*a)->next->val;
	third = (*a)->next->next->val;
	if (first > second && second > third)
	{
		sa(a, bench);
		rra(a, bench);
	}
	else if (first > second && first < third)
		sa(a, bench);
	else if (first > second && second < third)
		ra(a, bench);
	else if (first < second && first > third)
		rra(a, bench);
	else
	{
		sa(a, bench);
		ra(a, bench);
	}
}

void	tiny_sort(t_stack **a, t_stack **b, t_bench *bench, int size)
{
	int	pos;

	while (size > 3)
	{
		pos = get_min_pos(*a);
		if (pos <= size / 2)
		{
			while (pos > 0)
			{
				ra(a, bench);
				pos--;
			}
		}
		else
		{
			pos = size - pos;
			while (pos-- > 0)
				rra(a, bench);
		}
		pb(a, b, bench);
		size--;
	}
	sort_stack_3(a, bench);
}
