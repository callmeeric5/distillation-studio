/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   main.c                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: ericwindsor <ericwindsor@student.42.fr>    +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/07/07 23:05:00 by ericwindsor       #+#    #+#             */
/*   Updated: 2026/07/07 23:05:00 by ericwindsor      ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "codexion.h"

static void	print_usage(void)
{
	fprintf(stderr, "Usage: ./codexion number_of_coders time_to_burnout ");
	fprintf(stderr, "time_to_compile time_to_debug time_to_refactor ");
	fprintf(stderr, "number_of_compiles_required dongle_cooldown ");
	fprintf(stderr, "scheduler\n");
}

int	main(int argc, char **argv)
{
	t_config	config;
	t_sim		sim;

	if (!parse_args(argc, argv, &config))
	{
		print_usage();
		return (1);
	}
	if (!init_sim(&sim, config))
	{
		fprintf(stderr, "Error: initialization failed\n");
		destroy_sim(&sim);
		return (1);
	}
	if (!run_sim(&sim))
	{
		fprintf(stderr, "Error: thread creation failed\n");
		destroy_sim(&sim);
		return (1);
	}
	destroy_sim(&sim);
	return (0);
}
