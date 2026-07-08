/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   heap_order.c                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: ericwindsor <ericwindsor@student.42.fr>    +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/07/07 23:05:00 by ericwindsor       #+#    #+#             */
/*   Updated: 2026/07/07 23:05:00 by ericwindsor      ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "codexion.h"

static int	request_before(t_heap *heap, t_request *a, t_request *b)
{
	if (heap->sim->config.scheduler == CODEX_EDF
		&& a->deadline != b->deadline)
		return (a->deadline < b->deadline);
	if (a->sequence != b->sequence)
		return (a->sequence < b->sequence);
	return (a->coder->id < b->coder->id);
}

static void	swap_requests(t_request **a, t_request **b)
{
	t_request	*tmp;

	tmp = *a;
	*a = *b;
	*b = tmp;
}

void	heap_up(t_heap *heap, int index)
{
	int	parent;

	while (index > 0)
	{
		parent = (index - 1) / 2;
		if (!request_before(heap, heap->items[index], heap->items[parent]))
			return ;
		swap_requests(&heap->items[index], &heap->items[parent]);
		index = parent;
	}
}

void	heap_down(t_heap *heap, int index)
{
	int	left;
	int	right;
	int	best;

	while (1)
	{
		left = index * 2 + 1;
		right = index * 2 + 2;
		best = index;
		if (left < heap->size
			&& request_before(heap, heap->items[left], heap->items[best]))
			best = left;
		if (right < heap->size
			&& request_before(heap, heap->items[right], heap->items[best]))
			best = right;
		if (best == index)
			return ;
		swap_requests(&heap->items[index], &heap->items[best]);
		index = best;
	}
}
