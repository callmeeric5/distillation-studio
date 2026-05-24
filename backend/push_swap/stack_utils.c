
#include "push_swap.h"

size_t	get_stack_size(t_stack *stack)
{
	size_t	size;

	size = 0;
	while (stack)
	{
		size++;
		stack = stack->next;
	}
	return (size);
}

int	is_sorted_stack(t_stack *stack)
{
	t_stack	*curr;

	curr = stack;
	while (curr && curr->next)
	{
		if (curr->val > curr->next->val)
			return (0);
		curr = curr->next;
	}
	return (1);
}

void	clear_stack(t_stack **stack)
{
	t_stack	*next;

	if (!stack || !*stack)
		return ;
	while (*stack)
	{
		next = (*stack)->next;
		free(*stack);
		*stack = next;
	}
}

void	display_stack_error(t_stack **stack)
{
	write(2, "Error\n", 6);
	clear_stack(stack);
	exit(1);
}

void	push_stack(t_stack **stack, int val)
{
	t_stack	*node;
	t_stack	*tail;

	node = (t_stack *)malloc(sizeof(t_stack));
	if (!node)
		display_stack_error(stack);
	node->val = val;
	node->next = NULL;
	node->prev = NULL;
	node->index = 0;
	if (!*stack)
	{
		*stack = node;
		return ;
	}
	tail = *stack;
	while (tail->next)
		tail = tail->next;
	tail->next = node;
	node->prev = tail;
}
