

#include "push_swap.h"

void	sa(t_stack **a, t_bench *bench)
{
	swap(a);
	write(1, "sa\n", 3);
	bench->sa_c++;
}

void	pa(t_stack **b, t_stack **a, t_bench *bench)
{
	push(b, a);
	write(1, "pa\n", 3);
	bench->pa_c++;
}

void	ra(t_stack **a, t_bench *bench)
{
	rotate(a);
	write(1, "ra\n", 3);
	bench->ra_c++;
}

void	rra(t_stack **a, t_bench *bench)
{
	reverse_rotate(a);
	write(1, "rra\n", 4);
	bench->rra_c++;
}
