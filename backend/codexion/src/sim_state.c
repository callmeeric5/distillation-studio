/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   sim_state.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: ericwindsor <ericwindsor@student.42.fr>    +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/07/07 23:05:00 by ericwindsor       #+#    #+#             */
/*   Updated: 2026/07/07 23:05:00 by ericwindsor      ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "codexion.h"

void	sim_wake_all(t_sim *sim)
{
	int	i;

	i = 0;
	while (i < sim->config.coders_count)
	{
		pthread_cond_broadcast(&sim->coders[i].cond);
		i++;
	}
}

void	sim_log_state(t_sim *sim, int id, char *message)
{
	int	should_print;

	pthread_mutex_lock(&sim->log_lock);
	pthread_mutex_lock(&sim->lock);
	should_print = (!sim->stop || strcmp(message, "burned out") == 0);
	pthread_mutex_unlock(&sim->lock);
	if (should_print)
		printf("%ld %d %s\n", sim_time(sim), id, message);
	pthread_mutex_unlock(&sim->log_lock);
}

int	sim_is_stopped(t_sim *sim)
{
	int	stopped;

	pthread_mutex_lock(&sim->lock);
	stopped = sim->stop;
	pthread_mutex_unlock(&sim->lock);
	return (stopped);
}

void	sim_sleep(t_sim *sim, long ms)
{
	long	end;

	end = now_ms() + ms;
	while (!sim_is_stopped(sim) && now_ms() < end)
		usleep(500);
}

void	sim_set_wait_timeout(struct timespec *time)
{
	struct timeval	now;

	gettimeofday(&now, NULL);
	time->tv_sec = now.tv_sec;
	time->tv_nsec = (now.tv_usec + 2000) * 1000;
	if (time->tv_nsec >= 1000000000)
	{
		time->tv_sec++;
		time->tv_nsec -= 1000000000;
	}
}
