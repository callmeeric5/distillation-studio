
#include "push_swap.h"

static void	swap_num(int *a, int *b)
{
	int	temp;

	temp = *a;
	*a = *b;
	*b = temp;
}

static int	partition(int *arr, int low, int high)
{
	int	i;
	int	j;
	int	pivot;

	i = low;
	j = high;
	pivot = arr[i];
	while (1)
	{
		while (arr[i] < pivot)
			i++;
		while (arr[j] > pivot)
			j--;
		if (i >= j)
			return (j);
		swap_num(&arr[i], &arr[j]);
		i++;
		j--;
	}
}

void	quick_sort(int *arr, int low, int high)
{
	int	pivot_idx;

	if (low >= high)
		return ;
	pivot_idx = partition(arr, low, high);
	quick_sort(arr, low, pivot_idx);
	quick_sort(arr, pivot_idx + 1, high);
}
