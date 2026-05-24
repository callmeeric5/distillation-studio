
#include "push_swap.h"

static int	*create_array(t_stack *stack)
{
	size_t	size;
	int		*arr;
	size_t	i;

	i = 0;
	if (!stack)
		return (NULL);
	size = get_stack_size(stack);
	arr = malloc(sizeof(int) * size);
	if (!arr)
		return (NULL);
	while (stack)
	{
		arr[i] = stack->val;
		i++;
		stack = stack->next;
	}
	quick_sort(arr, 0, size - 1);
	return (arr);
}

void	init_stack_idx(t_stack **stack)
{
	int		*arr;
	int		i;
	int		size;
	t_stack	*curr;

	arr = create_array(*stack);
	if (!arr)
		return ;
	size = get_stack_size(*stack);
	curr = *stack;
	while (curr)
	{
		i = 0;
		while (i < size)
		{
			if (curr->val == arr[i])
			{
				curr->index = i;
				break ;
			}
			i++;
		}
		curr = curr->next;
	}
	free(arr);
}

void	ft_putstr_fd(char *s, int fd)
{
	int	i;

	i = 0;
	while (s[i])
	{
		write(fd, &s[i], 1);
		i++;
	}
}

void	ft_putnbr_fd(int n, int fd)
{
	long	nbl;
	char	c[50];
	short	i;

	nbl = n;
	i = 0;
	if (0 == n)
	{
		write(fd, "0", 1);
		return ;
	}
	if (nbl < 0)
	{
		nbl *= -1;
		write(fd, "-", 1);
	}
	while (nbl)
	{
		c[i++] = (nbl % 10) + 48;
		nbl /= 10;
	}
	while (i > 0)
		write(fd, &c[--i], 1);
}
