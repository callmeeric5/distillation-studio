
#include "push_swap.h"

int	get_min_val_stack(t_stack *stack)
{
	int	min;

	min = stack->val;
	while (stack)
	{
		if (stack->val < min)
			min = stack->val;
		stack = stack->next;
	}
	return (min);
}

int	*stack_to_array(t_stack *a)
{
	int	*arr;
	int	i;
	int	size;

	size = get_stack_size(a);
	arr = malloc(sizeof(int) * size);
	if (!arr)
		return (NULL);
	i = 0;
	while (a)
	{
		arr[i++] = a->val;
		a = a->next;
	}
	return (arr);
}

void	ft_sort_int_tab(int *tab, int size)
{
	int	i;
	int	j;
	int	k;
	int	tmp;

	k = 0;
	i = 0;
	while (k < size - 1)
	{
		j = i;
		while (i < size)
		{
			if (tab[i] < tab[j])
				j = i;
			i++;
		}
		if (tab[k] > tab[j])
		{
			tmp = tab[k];
			tab[k] = tab[j];
			tab[j] = tmp;
		}
		k++;
		i = k;
	}
}

void	fill_tab_chunks(int *chunks_tab, int nb_chunks, int size_stack,
		int *arr)
{
	int	i;
	int	index;

	i = 0;
	while (i < nb_chunks)
	{
		index = ((i + 1) * size_stack) / nb_chunks - 1;
		if (index < 0)
			index = 0;
		if (index >= size_stack)
			index = size_stack - 1;
		chunks_tab[i] = arr[index];
		i++;
	}
}
