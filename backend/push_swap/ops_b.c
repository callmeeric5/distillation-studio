
#include "push_swap.h"

void	sb(t_stack **b, t_bench *bench)
{
	swap(b);
	write(1, "sb\n", 3);
	bench->sb_c++;
}

void	pb(t_stack **a, t_stack **b, t_bench *bench)
{
	push(a, b);
	write(1, "pb\n", 3);
	bench->pb_c++;
}

void	rb(t_stack **b, t_bench *bench)
{
	rotate(b);
	write(1, "rb\n", 3);
	bench->rb_c++;
}

void	rrb(t_stack **b, t_bench *bench)
{
	reverse_rotate(b);
	write(1, "rrb\n", 4);
	bench->rrb_c++;
}
