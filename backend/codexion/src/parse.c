/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   parse.c                                            :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: ericwindsor <ericwindsor@student.42.fr>    +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/07/07 23:05:00 by ericwindsor       #+#    #+#             */
/*   Updated: 2026/07/07 23:05:00 by ericwindsor      ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "codexion.h"

static int	is_number(char *text)
{
	int	i;

	if (!text || !text[0])
		return (0);
	i = 0;
	while (text[i])
	{
		if (text[i] < '0' || text[i] > '9')
			return (0);
		i++;
	}
	return (1);
}

static long	read_long(char *text)
{
	long	value;
	int		i;

	value = 0;
	i = 0;
	while (text[i])
	{
		value = value * 10 + (text[i] - '0');
		if (value > 2147483647)
			return (-1);
		i++;
	}
	return (value);
}

static int	read_positive_int(char *text, int *out)
{
	long	value;

	if (!is_number(text))
		return (0);
	value = read_long(text);
	if (value <= 0)
		return (0);
	*out = (int)value;
	return (1);
}

static int	read_non_negative_long(char *text, long *out)
{
	long	value;

	if (!is_number(text))
		return (0);
	value = read_long(text);
	if (value < 0)
		return (0);
	*out = value;
	return (1);
}

int	parse_args(int argc, char **argv, t_config *config)
{
	if (argc != 9)
		return (0);
	memset(config, 0, sizeof(*config));
	if (!read_positive_int(argv[1], &config->coders_count))
		return (0);
	if (!read_non_negative_long(argv[2], &config->time_to_burnout))
		return (0);
	if (!read_non_negative_long(argv[3], &config->time_to_compile))
		return (0);
	if (!read_non_negative_long(argv[4], &config->time_to_debug))
		return (0);
	if (!read_non_negative_long(argv[5], &config->time_to_refactor))
		return (0);
	if (!read_positive_int(argv[6], &config->compiles_required))
		return (0);
	if (!read_non_negative_long(argv[7], &config->dongle_cooldown))
		return (0);
	if (strcmp(argv[8], "fifo") == 0)
		config->scheduler = CODEX_FIFO;
	else if (strcmp(argv[8], "edf") == 0)
		config->scheduler = CODEX_EDF;
	else
		return (0);
	return (1);
}
