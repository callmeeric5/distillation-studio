/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   heap.c                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: ericwindsor <ericwindsor@student.42.fr>    +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/07/07 23:05:00 by ericwindsor       #+#    #+#             */
/*   Updated: 2026/07/07 23:05:00 by ericwindsor      ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "codexion.h"

int	heap_init(t_heap *heap, int capacity, t_sim *sim)
{
	heap->items = malloc(sizeof(t_request *) * capacity);
	if (!heap->items)
		return (0);
	heap->size = 0;
	heap->capacity = capacity;
	heap->sim = sim;
	return (1);
}

void	heap_destroy(t_heap *heap)
{
	free(heap->items);
	heap->items = NULL;
	heap->size = 0;
	heap->capacity = 0;
}

int	heap_push(t_heap *heap, t_request *request)
{
	if (heap->size >= heap->capacity)
		return (0);
	heap->items[heap->size] = request;
	heap_up(heap, heap->size);
	heap->size++;
	return (1);
}

void	heap_remove(t_heap *heap, t_request *request)
{
	int	i;

	i = 0;
	while (i < heap->size)
	{
		if (heap->items[i] == request)
		{
			heap->size--;
			heap->items[i] = heap->items[heap->size];
			heap_down(heap, i);
			heap_up(heap, i);
			return ;
		}
		i++;
	}
}
