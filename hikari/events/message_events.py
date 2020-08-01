# -*- coding: utf-8 -*-
# cython: language_level=3str, boundscheck=False
# Copyright © Nekoka.tt 2019-2020
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
"""Events that fire if messages are sent/updated/deleted."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = [
    "MessagesEvent",
    "MessageEvent",
    "GuildMessageEvent",
    "PrivateMessageEvent",
    "MessageCreateEvent",
    "GuildMessageCreateEvent",
    "PrivateMessageCreateEvent",
    "MessageUpdateEvent",
    "GuildMessageUpdateEvent",
    "PrivateMessageUpdateEvent",
    "MessageDeleteEvent",
    "GuildMessageDeleteEvent",
    "PrivateMessageDeleteEvent",
    "MessageBulkDeleteEvent",
    "GuildMessageBulkDeleteEvent",
]

import abc
import typing

import attr

from hikari.events import base_events
from hikari.events import shard_events
from hikari.models import intents

if typing.TYPE_CHECKING:
    from hikari.api import shard as gateway_shard
    from hikari.models import messages
    from hikari.models import users
    from hikari.utilities import snowflake


@base_events.requires_intents(intents.Intent.GUILD_MESSAGES, intents.Intent.PRIVATE_MESSAGES)
@attr.s(kw_only=True, slots=True)
class MessagesEvent(shard_events.ShardEvent, abc.ABC):
    """Event base for any message-bound event."""

    @property
    @abc.abstractmethod
    def channel_id(self) -> snowflake.Snowflake:
        """ID of the channel that this event concerns.

        Returns
        -------
        hikari.utilities.snowflake.Snowflake
            The ID of the channel that this event concerns.
        """


@base_events.requires_intents(intents.Intent.GUILD_MESSAGES, intents.Intent.PRIVATE_MESSAGES)
@attr.s(kw_only=True, slots=True)
class MessageEvent(MessagesEvent, abc.ABC):
    """Event base for any event that concerns a single message."""

    @property
    @abc.abstractmethod
    def message_id(self) -> snowflake.Snowflake:
        """ID of the message that this event concerns.

        Returns
        -------
        hikari.utilities.snowflake.Snowflake
            The ID of the message that this event concerns.
        """


@base_events.requires_intents(intents.Intent.PRIVATE_MESSAGES)
@attr.s(kw_only=True, slots=True)
class PrivateMessageEvent(MessageEvent, abc.ABC):
    """Event base for any message-bound event in private messages."""


@base_events.requires_intents(intents.Intent.GUILD_MESSAGES)
@attr.s(kw_only=True, slots=True)
class GuildMessageEvent(MessageEvent, abc.ABC):
    """Event base for any message-bound event in guild messages."""

    @property
    @abc.abstractmethod
    def guild_id(self) -> snowflake.Snowflake:
        """ID of the guild that this event concerns.

        Returns
        -------
        hikari.utilities.snowflake.Snowflake
            The ID of the guild that this event concerns.
        """


@base_events.requires_intents(intents.Intent.GUILD_MESSAGES, intents.Intent.PRIVATE_MESSAGES)
@attr.s(kw_only=True, slots=True)
class MessageCreateEvent(MessageEvent, abc.ABC):
    """Event base for any message creation event."""

    @property
    @abc.abstractmethod
    def message(self) -> messages.Message:
        """Message that was sent in the event.

        Returns
        -------
        hikari.models.messages.Message
            The message object that was sent with this event.
        """

    @property
    def message_id(self) -> snowflake.Snowflake:
        # <<inherited docstring from MessageEvent>>.
        return self.message.id

    @property
    def channel_id(self) -> snowflake.Snowflake:
        # <<inherited docstring from MessageEvent>>.
        return self.message.channel_id

    @property
    def author_id(self) -> snowflake.Snowflake:
        """ID of the author that triggered this event.

        Returns
        -------
        hikari.utilities.snowflake.Snowflake
            The ID of the author that triggered this event concerns.
        """
        return self.message.author.id


@base_events.requires_intents(intents.Intent.GUILD_MESSAGES, intents.Intent.PRIVATE_MESSAGES)
@attr.s(kw_only=True, slots=True)
class MessageUpdateEvent(MessageEvent, abc.ABC):
    """Event base for any message update event."""

    @property
    @abc.abstractmethod
    def message(self) -> messages.PartialMessage:
        """Partial message that was sent in the event.

        !!! warning
            Unlike `MessageCreateEvent`, `MessageUpdateEvent.message` is an
            arbitrarily partial version of `hikari.models.messages.Message`
            where any field except `id` and `channel_id` may be set to
            `hikari.utilities.undefined.UndefinedType` (a singleton) to indicate
            that it has not been changed.

        Returns
        -------
        hikari.models.messages.PartialMessage
            The partially populated message object that was sent with this
            event.
        """

    @property
    def message_id(self) -> snowflake.Snowflake:
        # <<inherited docstring from MessageEvent>>.
        return self.message.id

    @property
    def author_id(self) -> snowflake.Snowflake:
        """ID of the author that triggered this event.

        Returns
        -------
        hikari.utilities.snowflake.Snowflake
            The ID of the author that triggered this event concerns.
        """
        # Looks like `author` is always present in this event variant.
        # TODO: verify that this is definitely present always.
        return typing.cast(users.PartialUser, self.message.author).id

    @property
    def channel_id(self) -> snowflake.Snowflake:
        # <<inherited docstring from MessageEvent>>.
        return self.message.channel_id


@base_events.requires_intents(intents.Intent.GUILD_MESSAGES, intents.Intent.PRIVATE_MESSAGES)
@attr.s(kw_only=True, slots=True)
class MessageDeleteEvent(MessageEvent, abc.ABC):
    """Event base for any message delete event."""

    @property
    @abc.abstractmethod
    def message(self) -> messages.PartialMessage:
        """Partial message that was sent in the event.

        !!! warning
            Unlike `MessageCreateEvent`, `message` is a severely limited partial
            version of `hikari.models.messages.Message`. The only attributes
            that will not be `hikari.utilities.undefined.UNDEFINED` will be
            `id`, `channel_id`, and `guild_id` if the message was in a guild.
            This is a limitation of Discord.

            Furthermore, this partial message will represent a message that no
            longer exists. Thus, attempting to edit/delete/react or un-react to
            this message or attempting to fetch the full version will result
            in a `hikari.errors.NotFound` being raised.

        Returns
        -------
        hikari.models.messages.PartialMessage
            The partially populated message object that was sent with this
            event.
        """

    @property
    def message_id(self) -> snowflake.Snowflake:
        # <<inherited docstring from MessageEvent>>.
        return self.message.id

    @property
    def channel_id(self) -> snowflake.Snowflake:
        # <<inherited docstring from MessagesEvent>>.
        return self.message.channel_id


@base_events.requires_intents(intents.Intent.GUILD_MESSAGES)
@attr.s(kw_only=True, slots=True)
class GuildMessageCreateEvent(GuildMessageEvent, MessageCreateEvent):
    """Event triggered when a message is sent to a guild channel."""

    shard: gateway_shard.IGatewayShard = attr.ib()
    # <<inherited docstring from ShardEvent>>.

    message: messages.Message = attr.ib()
    # <<inherited docstring from MessageCreateEvent>>.

    @property
    def guild_id(self) -> snowflake.Snowflake:
        # <<inherited docstring from GuildMessageEvent>>.
        # Always present in this event.
        return typing.cast("snowflake.Snowflake", self.message.guild_id)


@base_events.requires_intents(intents.Intent.PRIVATE_MESSAGES)
@attr.s(kw_only=True, slots=True)
class PrivateMessageCreateEvent(PrivateMessageEvent, MessageCreateEvent):
    """Event triggered when a message is sent to a private channel."""

    shard: gateway_shard.IGatewayShard = attr.ib()
    # <<inherited docstring from ShardEvent>>.

    message: messages.Message = attr.ib()
    # <<inherited docstring from MessageCreateEvent>>.


@base_events.requires_intents(intents.Intent.GUILD_MESSAGES)
@attr.s(kw_only=True, slots=True)
class GuildMessageUpdateEvent(GuildMessageEvent, MessageUpdateEvent):
    """Event triggered when a message is updated in a guild channel."""

    shard: gateway_shard.IGatewayShard = attr.ib()
    # <<inherited docstring from ShardEvent>>.

    message: messages.PartialMessage = attr.ib()
    # <<inherited docstring from MessageUpdateEvent>>.

    @property
    def guild_id(self) -> snowflake.Snowflake:
        # <<inherited docstring from GuildMessageEvent>>.
        # Always present in this event.
        return typing.cast("snowflake.Snowflake", self.message.guild_id)


@base_events.requires_intents(intents.Intent.PRIVATE_MESSAGES)
@attr.s(kw_only=True, slots=True)
class PrivateMessageUpdateEvent(PrivateMessageEvent, MessageUpdateEvent):
    """Event triggered when a message is updated in a private channel."""

    shard: gateway_shard.IGatewayShard = attr.ib()
    # <<inherited docstring from ShardEvent>>.

    message: messages.PartialMessage = attr.ib()
    # <<inherited docstring from MessageUpdateEvent>>.


@base_events.requires_intents(intents.Intent.GUILD_MESSAGES)
@attr.s(kw_only=True, slots=True)
class GuildMessageDeleteEvent(GuildMessageEvent, MessageDeleteEvent):
    """Event triggered when a message is deleted from a guild channel."""

    shard: gateway_shard.IGatewayShard = attr.ib()
    # <<inherited docstring from ShardEvent>>.

    message: messages.PartialMessage = attr.ib()
    # <<inherited docstring from MessageDeleteEvent>>.

    @property
    def guild_id(self) -> snowflake.Snowflake:
        # <<inherited docstring from GuildMessageEvent>>.
        # Always present in this event.
        return typing.cast("snowflake.Snowflake", self.message.guild_id)


@attr.s(kw_only=True, slots=True)
@base_events.requires_intents(intents.Intent.PRIVATE_MESSAGES)
class PrivateMessageDeleteEvent(PrivateMessageEvent, MessageDeleteEvent):
    """Event triggered when a message is deleted from a private channel."""

    shard: gateway_shard.IGatewayShard = attr.ib()
    # <<inherited docstring from ShardEvent>>.

    message: messages.PartialMessage = attr.ib()
    # <<inherited docstring from MessageDeleteEvent>>.


# NOTE: if this ever has a private channel equivalent implemented, this intents
# constraint should be relaxed.
@attr.s(kw_only=True, slots=True)
@base_events.requires_intents(intents.Intent.GUILD_MESSAGES)
class MessageBulkDeleteEvent(MessagesEvent, abc.ABC):
    """Event triggered when messages are bulk-deleted from a channel.

    !!! note
        There is only a guild equivalent of this event at the time of writing.
        However, Discord appear to not be ruling out that this ability may
        be implemented for private channels in the future. Thus, this base
        exists for future compatibility and consistency.

        If you care about the event occurring in a guild specifically, you
        should use the `GuildMessageBulkDeleteEvent`. Otherwise, using this
        event base is acceptable.

        See https://github.com/discord/discord-api-docs/issues/1633 for
        Discord's response.
    """


@attr.s(kw_only=True, slots=True)
@base_events.requires_intents(intents.Intent.GUILD_MESSAGES)
class GuildMessageBulkDeleteEvent(MessageBulkDeleteEvent):
    """Event triggered when messages are bulk-deleted from a guild channel."""

    shard: gateway_shard.IGatewayShard = attr.ib()
    # <<inherited docstring from ShardEvent>>.

    channel_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from MessagesEvent>>.

    guild_id: snowflake.Snowflake = attr.ib()
    """ID of the guild that this event concerns.

    Returns
    -------
    hikari.utilities.snowflake.Snowflake
        The ID of the guild that this event concerns.
    """

    message_ids: typing.Sequence[snowflake.Snowflake] = attr.ib()
    """Sequence of message IDs that were bulk deleted.

    Returns
    -------
    typing.Sequence[hikari.utilities.snowflake.Snowflake]
        A sequence of message IDs that were bulk deleted.
    """
