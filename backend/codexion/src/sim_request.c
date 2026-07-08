/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   sim_request.c                                      :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: ericwindsor <ericwindsor@student.42.fr>    +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/07/07 23:05:00 by ericwindsor       #+#    #+#             */
/*   Updated: 2026/07/07 23:05:00 by ericwindsor      ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "codexion.h"

static int	request_ready(t_request *request)
{
	t_dongle	*left;
	t_dongle	*right;
	t_request	*left_first;
	t_request	*right_first;
	long		time;

	left = request->coder->left;
	right = request->coder->right;
	if (left == right)
		return (0);
	time = now_ms();
	if (left->in_use || right->in_use)
		return (0);
	if (left->cooldown_until > time || right->cooldown_until > time)
		return (0);
	heap_peek(&left->waiting, &left_first);
	heap_peek(&right->waiting, &right_first);
	return (left_first == request && right_first == request);
}

static void	insert_request(t_coder *coder, t_request *request)
{
	t_sim	*sim;

	sim = coder->sim;
	request->coder = coder;
	request->sequence = sim->next_sequence++;
	request->deadline = coder->last_compile_start
		+ sim->config.time_to_burnout;
	heap_push(&coder->left->waiting, request);
	if (coder->right != coder->left)
		heap_push(&coder->right->waiting, request);
}

static void	remove_request(t_coder *coder, t_request *request)
{
	if (heap_has(&coder->left->waiting, request))
		heap_remove(&coder->left->waiting, request);
	if (coder->right != coder->left
		&& heap_has(&coder->right->waiting, request))
		heap_remove(&coder->right->waiting, request);
}

static void	grant_request(t_coder *coder, t_request *request)
{
	remove_request(coder, request);
	coder->left->in_use = 1;
	coder->right->in_use = 1;
	coder->last_compile_start = now_ms();
}

int	take_dongles(t_coder *coder)
{
	t_sim			*sim;
	t_request		request;
	struct timespec	timeout;

	sim = coder->sim;
	pthread_mutex_lock(&sim->lock);
	insert_request(coder, &request);
	while (!sim->stop && !request_ready(&request))
	{
		sim_set_wait_timeout(&timeout);
		pthread_cond_timedwait(&coder->cond, &sim->lock, &timeout);
	}
	if (sim->stop)
	{
		remove_request(coder, &request);
		pthread_mutex_unlock(&sim->lock);
		return (0);
	}
	grant_request(coder, &request);
	pthread_mutex_unlock(&sim->lock);
	sim_log_state(sim, coder->id, "has taken a dongle");
	sim_log_state(sim, coder->id, "has taken a dongle");
	sim_log_state(sim, coder->id, "is compiling");
	return (1);
}
