
#include "push_swap.h"

int	ft_strcmp(char *dst, char *src)
{
	int	i;

	i = 0;
	while (dst[i] == src[i] && dst[i])
		i++;
	return (dst[i] - src[i]);
}

int	extract_number(char **str, t_stack **stack)
{
	long	res;
	int		sign;
	int		i;

	res = 0;
	sign = 1;
	i = 0;
	if ((*str)[i] == '+' || (*str)[i] == '-')
	{
		if ((*str)[i] == '-')
			sign = -1;
		i++;
	}
	if (!((*str)[i] >= '0' && (*str)[i] <= '9'))
		display_stack_error(stack);
	while ((*str)[i] >= '0' && (*str)[i] <= '9')
	{
		res = (res * 10) + ((*str)[i] - '0');
		if ((res * sign) > INT_MAX || (res * sign) < INT_MIN)
			display_stack_error(stack);
		i++;
	}
	*str += i;
	return ((res * sign));
}

t_algo_type	extract_strategy(char *str)
{
	if (ft_strcmp(str, "--simple") == 0)
		return (SIMPLE);
	else if (ft_strcmp(str, "--medium") == 0)
		return (MEDIUM);
	else if (ft_strcmp(str, "--complex") == 0)
		return (COMPLEX);
	else if (ft_strcmp(str, "--adaptive") == 0)
		return (ADAPTIVE);
	return (NONE);
}
