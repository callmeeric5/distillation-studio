/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   heap_query.c                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: ericwindsor <ericwindsor@student.42.fr>    +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/07/07 23:05:00 by ericwindsor       #+#    #+#             */
/*   Updated: 2026/07/07 23:05:00 by ericwindsor      ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "codexion.h"

int	heap_has(t_heap *heap, t_request *request)
{
	int	i;

	i = 0;
	while (i < heap->size)
	{
		if (heap->items[i] == request)
			return (1);
		i++;
	}
	return (0);
}

void	heap_peek(t_heap *heap, t_request **request)
{
	if (heap->size == 0)
		*request = NULL;
	else
		*request = heap->items[0];
}
