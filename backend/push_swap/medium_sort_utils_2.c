
#include "push_swap.h"

int	*set_chunks(t_stack **a, int nb_chunks)
{
	size_t	size_stack;
	int		*arr;
	int		*chunks_tab;

	arr = stack_to_array(*a);
	if (!arr)
		return (NULL);
	size_stack = get_stack_size(*a);
	ft_sort_int_tab(arr, size_stack);
	chunks_tab = malloc(sizeof(int) * nb_chunks);
	if (!chunks_tab)
	{
		free(arr);
		return (NULL);
	}
	fill_tab_chunks(chunks_tab, nb_chunks, size_stack, arr);
	free(arr);
	return (chunks_tab);
}

int	get_val_pos_stack(t_stack *stack, int val)
{
	int	pos;

	pos = 0;
	while (stack && stack->val != val)
	{
		pos++;
		stack = stack->next;
	}
	return (pos);
}

t_stack	*last_node(t_stack *stack)
{
	if (!stack)
		return (NULL);
	while (stack->next)
		stack = stack->next;
	return (stack);
}

int	get_max_val_stack(t_stack *stack)
{
	int	max;

	max = stack->val;
	while (stack)
	{
		if (stack->val > max)
			max = stack->val;
		stack = stack->next;
	}
	return (max);
}

int	find_target_in_b(t_stack *stack, int val)
{
	int	target;
	int	target_pos;
	int	i;
	int	found;

	i = 0;
	target_pos = -1;
	found = 0;
	while (stack)
	{
		if (stack->val < val)
		{
			if (!found || stack->val > target)
			{
				target = stack->val;
				target_pos = i;
				found = 1;
			}
		}
		i++;
		stack = stack->next;
	}
	return (target_pos);
}
