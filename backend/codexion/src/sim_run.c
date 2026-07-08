/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   sim_run.c                                          :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: ericwindsor <ericwindsor@student.42.fr>    +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/07/07 23:05:00 by ericwindsor       #+#    #+#             */
/*   Updated: 2026/07/07 23:05:00 by ericwindsor      ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "codexion.h"

static int	start_coders(t_sim *sim)
{
	int	i;

	i = 0;
	while (i < sim->config.coders_count)
	{
		if (pthread_create(&sim->coders[i].thread, NULL,
				coder_routine, &sim->coders[i]) != 0)
			return (0);
		i++;
	}
	return (1);
}

static void	join_coders(t_sim *sim)
{
	int	i;

	i = 0;
	while (i < sim->config.coders_count)
	{
		pthread_join(sim->coders[i].thread, NULL);
		i++;
	}
}

int	run_sim(t_sim *sim)
{
	if (!start_coders(sim))
		return (0);
	if (pthread_create(&sim->monitor, NULL, monitor_routine, sim) != 0)
		return (0);
	join_coders(sim);
	pthread_join(sim->monitor, NULL);
	return (1);
}

void	destroy_sim(t_sim *sim)
{
	int	i;

	i = 0;
	if (sim->coders)
	{
		while (i < sim->config.coders_count)
			pthread_cond_destroy(&sim->coders[i++].cond);
	}
	i = 0;
	if (sim->dongles)
	{
		while (i < sim->config.coders_count)
			heap_destroy(&sim->dongles[i++].waiting);
	}
	free(sim->coders);
	free(sim->dongles);
	pthread_mutex_destroy(&sim->lock);
	pthread_mutex_destroy(&sim->log_lock);
}
