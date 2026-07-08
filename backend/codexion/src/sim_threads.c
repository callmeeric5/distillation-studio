/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   sim_threads.c                                      :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: ericwindsor <ericwindsor@student.42.fr>    +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/07/07 23:05:00 by ericwindsor       #+#    #+#             */
/*   Updated: 2026/07/07 23:05:00 by ericwindsor      ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "codexion.h"

static void	*single_coder(t_coder *coder)
{
	sim_log_state(coder->sim, coder->id, "has taken a dongle");
	while (!sim_is_stopped(coder->sim))
		usleep(1000);
	return (NULL);
}

void	*coder_routine(void *data)
{
	t_coder	*coder;
	t_sim	*sim;

	coder = data;
	sim = coder->sim;
	if (sim->config.coders_count == 1)
		return (single_coder(coder));
	while (!sim_is_stopped(sim))
	{
		if (!take_dongles(coder))
			break ;
		sim_sleep(sim, sim->config.time_to_compile);
		release_dongles(coder);
		sim_log_state(sim, coder->id, "is debugging");
		sim_sleep(sim, sim->config.time_to_debug);
		sim_log_state(sim, coder->id, "is refactoring");
		sim_sleep(sim, sim->config.time_to_refactor);
	}
	return (NULL);
}

static int	monitor_check_coder(t_sim *sim, int index)
{
	long	deadline;
	long	time;

	pthread_mutex_lock(&sim->lock);
	deadline = sim->coders[index].last_compile_start
		+ sim->config.time_to_burnout;
	time = now_ms();
	if (!sim->stop && time >= deadline)
	{
		sim->stop = 1;
		sim_wake_all(sim);
		pthread_mutex_unlock(&sim->lock);
		sim_log_state(sim, sim->coders[index].id, "burned out");
		return (1);
	}
	pthread_mutex_unlock(&sim->lock);
	return (0);
}

void	*monitor_routine(void *data)
{
	t_sim	*sim;
	int		i;

	sim = data;
	while (!sim_is_stopped(sim))
	{
		i = 0;
		while (i < sim->config.coders_count && !sim_is_stopped(sim))
		{
			if (monitor_check_coder(sim, i))
				return (NULL);
			i++;
		}
		usleep(1000);
	}
	return (NULL);
}
