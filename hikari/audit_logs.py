#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
"""Components and entities that are used to describe audit logs on Discord."""
__all__ = [
    "AuditLog",
    "AuditLogChange",
    "AuditLogChangeKey",
    "AuditLogEntry",
    "AuditLogEventType",
    "AuditLogIterator",
    "BaseAuditLogEntryInfo",
    "ChannelOverwriteEntryInfo",
    "get_entry_info_entity",
    "MemberDisconnectEntryInfo",
    "MemberMoveEntryInfo",
    "MemberPruneEntryInfo",
    "MessageBulkDeleteEntryInfo",
    "MessageDeleteEntryInfo",
    "MessagePinEntryInfo",
]

import abc
import copy
import datetime
import enum
import typing

import attr

from hikari import bases
from hikari import channels
from hikari import colors
from hikari import guilds
from hikari import permissions
from hikari import users as _users
from hikari import webhooks as _webhooks
from hikari.internal import conversions
from hikari.internal import marshaller
from hikari.internal import more_collections
from hikari.internal import more_typing


class AuditLogChangeKey(str, enum.Enum):
    """Commonly known and documented keys for audit log change objects.

    Others may exist. These should be expected to default to the raw string
    Discord provided us.
    """

    NAME = "name"
    ICON_HASH = "icon_hash"
    SPLASH_HASH = "splash_hash"
    OWNER_ID = "owner_id"
    REGION = "region"
    AFK_CHANNEL_ID = "afk_channel_id"
    AFK_TIMEOUT = "afk_timeout"
    MFA_LEVEL = "mfa_level"
    VERIFICATION_LEVEL = "verification_level"
    EXPLICIT_CONTENT_FILTER = "explicit_content_filter"
    DEFAULT_MESSAGE_NOTIFICATIONS = "default_message_notifications"
    VANITY_URL_CODE = "vanity_url_code"
    ADD_ROLE_TO_MEMBER = "$add"
    REMOVE_ROLE_FROM_MEMBER = "$remove"
    PRUNE_DELETE_DAYS = "prune_delete_days"
    WIDGET_ENABLED = "widget_enabled"
    WIDGET_CHANNEL_ID = "widget_channel_id"
    POSITION = "position"
    TOPIC = "topic"
    BITRATE = "bitrate"
    PERMISSION_OVERWRITES = "permission_overwrites"
    NSFW = "nsfw"
    APPLICATION_ID = "application_id"
    PERMISSIONS = "permissions"
    COLOR = "color"
    HOIST = "hoist"
    MENTIONABLE = "mentionable"
    ALLOW = "allow"
    DENY = "deny"
    INVITE_CODE = "code"
    CHANNEL_ID = "channel_id"
    INVITER_ID = "inviter_id"
    MAX_USES = "max_uses"
    USES = "uses"
    MAX_AGE = "max_age"
    TEMPORARY = "temporary"
    DEAF = "deaf"
    MUTE = "mute"
    NICK = "nick"
    AVATAR_HASH = "avatar_hash"
    ID = "id"
    TYPE = "type"
    ENABLE_EMOTICONS = "enable_emoticons"
    EXPIRE_BEHAVIOR = "expire_behavior"
    EXPIRE_GRACE_PERIOD = "expire_grace_period"
    RATE_LIMIT_PER_USER = "rate_limit_per_user"
    SYSTEM_CHANNEL_ID = "system_channel_id"

    #: Alias for "COLOR"
    COLOUR = COLOR

    def __str__(self) -> str:
        return self.name

    __repr__ = __str__


AUDIT_LOG_ENTRY_CONVERTERS = {
    AuditLogChangeKey.OWNER_ID: bases.Snowflake.deserialize,
    AuditLogChangeKey.AFK_CHANNEL_ID: bases.Snowflake.deserialize,
    AuditLogChangeKey.AFK_TIMEOUT: lambda payload: datetime.timedelta(seconds=payload),
    AuditLogChangeKey.MFA_LEVEL: guilds.GuildMFALevel,
    AuditLogChangeKey.VERIFICATION_LEVEL: guilds.GuildVerificationLevel,
    AuditLogChangeKey.EXPLICIT_CONTENT_FILTER: guilds.GuildExplicitContentFilterLevel,
    AuditLogChangeKey.DEFAULT_MESSAGE_NOTIFICATIONS: guilds.GuildMessageNotificationsLevel,
    AuditLogChangeKey.ADD_ROLE_TO_MEMBER: lambda payload: {
        role.id: role for role in map(guilds.PartialGuildRole.deserialize, payload)
    },
    AuditLogChangeKey.REMOVE_ROLE_FROM_MEMBER: lambda payload: {
        role.id: role for role in map(guilds.PartialGuildRole.deserialize, payload)
    },
    AuditLogChangeKey.PRUNE_DELETE_DAYS: lambda payload: datetime.timedelta(days=int(payload)),
    AuditLogChangeKey.WIDGET_CHANNEL_ID: bases.Snowflake.deserialize,
    AuditLogChangeKey.POSITION: int,
    AuditLogChangeKey.BITRATE: int,
    AuditLogChangeKey.PERMISSION_OVERWRITES: lambda payload: {
        overwrite.id: overwrite for overwrite in map(channels.PermissionOverwrite.deserialize, payload)
    },
    AuditLogChangeKey.APPLICATION_ID: bases.Snowflake.deserialize,
    AuditLogChangeKey.PERMISSIONS: permissions.Permission,
    AuditLogChangeKey.COLOR: colors.Color,
    AuditLogChangeKey.ALLOW: permissions.Permission,
    AuditLogChangeKey.DENY: permissions.Permission,
    AuditLogChangeKey.CHANNEL_ID: bases.Snowflake.deserialize,
    AuditLogChangeKey.INVITER_ID: bases.Snowflake.deserialize,
    AuditLogChangeKey.MAX_USES: lambda payload: int(payload) if payload > 0 else float("inf"),
    AuditLogChangeKey.USES: int,
    AuditLogChangeKey.MAX_AGE: lambda payload: datetime.timedelta(seconds=payload) if payload > 0 else None,
    AuditLogChangeKey.ID: bases.Snowflake.deserialize,
    AuditLogChangeKey.TYPE: str,
    AuditLogChangeKey.ENABLE_EMOTICONS: bool,
    AuditLogChangeKey.EXPIRE_BEHAVIOR: guilds.IntegrationExpireBehaviour,
    AuditLogChangeKey.EXPIRE_GRACE_PERIOD: lambda payload: datetime.timedelta(days=payload),
    AuditLogChangeKey.RATE_LIMIT_PER_USER: lambda payload: datetime.timedelta(seconds=payload),
    AuditLogChangeKey.SYSTEM_CHANNEL_ID: bases.Snowflake.deserialize,
}


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class AuditLogChange(bases.HikariEntity, marshaller.Deserializable):
    """Represents a change made to an audit log entry's target entity.

    Attributes
    ----------
    new_value : typing.Any, optional
        The new value of the key, if something was added or changed.
    old_value : typing.Any, optional
        The old value of the key, if something was removed or changed.
    key : typing.Union [ AuditLogChangeKey, str ]
        The name of the audit log change's key.
    """

    new_value: typing.Optional[typing.Any] = marshaller.attrib()
    old_value: typing.Optional[typing.Any] = marshaller.attrib()
    key: typing.Union[AuditLogChangeKey, str] = marshaller.attrib()

    @classmethod
    def deserialize(cls, payload: typing.Mapping[str, str]) -> "AuditLogChange":
        """Deserialize this model from a raw payload."""
        key = conversions.try_cast(payload["key"], AuditLogChangeKey, payload["key"])
        new_value = payload.get("new_value")
        old_value = payload.get("old_value")
        if value_converter := AUDIT_LOG_ENTRY_CONVERTERS.get(key):
            new_value = value_converter(new_value) if new_value is not None else None
            old_value = value_converter(old_value) if old_value is not None else None

        # noinspection PyArgumentList
        return cls(key=key, new_value=new_value, old_value=old_value)


@enum.unique
class AuditLogEventType(enum.IntEnum):
    """The type of event that occurred."""

    GUILD_UPDATE = 1
    CHANNEL_CREATE = 10
    CHANNEL_UPDATE = 11
    CHANNEL_DELETE = 12
    CHANNEL_OVERWRITE_CREATE = 13
    CHANNEL_OVERWRITE_UPDATE = 14
    CHANNEL_OVERWRITE_DELETE = 15
    MEMBER_KICK = 20
    MEMBER_PRUNE = 21
    MEMBER_BAN_ADD = 22
    MEMBER_BAN_REMOVE = 23
    MEMBER_UPDATE = 24
    MEMBER_ROLE_UPDATE = 25
    MEMBER_MOVE = 26
    MEMBER_DISCONNECT = 27
    BOT_ADD = 28
    ROLE_CREATE = 30
    ROLE_UPDATE = 31
    ROLE_DELETE = 32
    INVITE_CREATE = 40
    INVITE_UPDATE = 41
    INVITE_DELETE = 42
    WEBHOOK_CREATE = 50
    WEBHOOK_UPDATE = 51
    WEBHOOK_DELETE = 52
    EMOJI_CREATE = 60
    EMOJI_UPDATE = 61
    EMOJI_DELETE = 62
    MESSAGE_DELETE = 72
    MESSAGE_BULK_DELETE = 73
    MESSAGE_PIN = 74
    MESSAGE_UNPIN = 75
    INTEGRATION_CREATE = 80
    INTEGRATION_UPDATE = 81
    INTEGRATION_DELETE = 82


# Ignore docstring not starting in an imperative mood
def register_audit_log_entry_info(
    type_: AuditLogEventType, *additional_types: AuditLogEventType
) -> typing.Callable[[typing.Type["BaseAuditLogEntryInfo"]], typing.Type["BaseAuditLogEntryInfo"]]:  # noqa: D401
    """Generates a decorator for defined audit log entry info entities.

    Allows them to be associated with given entry type(s).

    Parameters
    ----------
    type_ : AuditLogEventType
        An entry types to associate the entity with.
    *additional_types : AuditLogEventType
        Extra entry types to associate the entity with.

    Returns
    -------
    ``decorator(T) -> T``
        The decorator to decorate the class with.
    """

    def decorator(cls):
        mapping = getattr(register_audit_log_entry_info, "types", {})
        for t in [type_, *additional_types]:
            mapping[t] = cls
        setattr(register_audit_log_entry_info, "types", mapping)
        return cls

    return decorator


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class BaseAuditLogEntryInfo(bases.HikariEntity, marshaller.Deserializable, abc.ABC):
    """A base object that all audit log entry info objects will inherit from."""


@register_audit_log_entry_info(
    AuditLogEventType.CHANNEL_OVERWRITE_CREATE,
    AuditLogEventType.CHANNEL_OVERWRITE_UPDATE,
    AuditLogEventType.CHANNEL_OVERWRITE_DELETE,
)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class ChannelOverwriteEntryInfo(BaseAuditLogEntryInfo):
    """Represents the extra information for overwrite related audit log entries.

    Will be attached to the overwrite create, update and delete audit log
    entries.

    Attributes
    ----------
    id : hikari.snowflakes.Snowflake
        The ID of the overwrite being updated, added or removed (and the entity
        it targets).
    type : hikari.channels.PermissionOverwriteType
        The type of entity this overwrite targets.
    role_name : str, optional
        The name of the role this overwrite targets, if it targets a role.
    """

    id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    type: channels.PermissionOverwriteType = marshaller.attrib(deserializer=channels.PermissionOverwriteType)
    role_name: typing.Optional[str] = marshaller.attrib(deserializer=str, if_undefined=None, default=None)


@register_audit_log_entry_info(AuditLogEventType.MESSAGE_PIN, AuditLogEventType.MESSAGE_UNPIN)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MessagePinEntryInfo(BaseAuditLogEntryInfo):
    """The extra information for message pin related audit log entries.

    Will be attached to the message pin and message unpin audit log entries.

    Attributes
    ----------
    channel_id : hikari.snowflakes.Snowflake
        The ID of the guild text based channel where this pinned message is
        being added or removed.
    message_id : hikari.snowflakes.Snowflake
        The ID of the message that's being pinned or unpinned.
    """

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    message_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)


@register_audit_log_entry_info(AuditLogEventType.MEMBER_PRUNE)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MemberPruneEntryInfo(BaseAuditLogEntryInfo):
    """Represents the extra information attached to guild prune log entries.

    Attributes
    ----------
    delete_member_days : datetime.timedelta
        The timedelta of how many days members were pruned for inactivity based
        on.
    members_removed : int
        The number of members who were removed by this prune.
    """

    delete_member_days: datetime.timedelta = marshaller.attrib(
        deserializer=lambda payload: datetime.timedelta(days=int(payload))
    )
    members_removed: int = marshaller.attrib(deserializer=int)


@register_audit_log_entry_info(AuditLogEventType.MESSAGE_BULK_DELETE)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MessageBulkDeleteEntryInfo(BaseAuditLogEntryInfo):
    """Represents extra information for the message bulk delete audit entry.

    Attributes
    ----------
    count : int
        The amount of messages that were deleted.
    """

    count: int = marshaller.attrib(deserializer=int)


@register_audit_log_entry_info(AuditLogEventType.MESSAGE_DELETE)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MessageDeleteEntryInfo(MessageBulkDeleteEntryInfo):
    """Represents extra information attached to the message delete audit entry.

    Attributes
    ----------
    channel_id : hikari.snowflakes.Snowflake
        The guild text based channel where these message(s) were deleted.
    count : int
        The amount of messages that were deleted.
    """

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)


@register_audit_log_entry_info(AuditLogEventType.MEMBER_DISCONNECT)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MemberDisconnectEntryInfo(BaseAuditLogEntryInfo):
    """Represents extra information for the voice chat member disconnect entry.

    Attributes
    ----------
    count : int
        The amount of members who were disconnected from voice in this entry.
    """

    count: int = marshaller.attrib(deserializer=int)


@register_audit_log_entry_info(AuditLogEventType.MEMBER_MOVE)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MemberMoveEntryInfo(MemberDisconnectEntryInfo):
    """Represents extra information for the voice chat based member move entry.

    Attributes
    ----------
    channel_id : hikari.snowflakes.Snowflake
        The channel these member(s) were moved to.
    count : int
        The amount of members who were disconnected from voice in this entry.
    """

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)


class UnrecognisedAuditLogEntryInfo(BaseAuditLogEntryInfo):
    """Represents any audit log entry options that haven't been implemented."""

    def __init__(self, payload: typing.Mapping[str, str]) -> None:
        self.__dict__.update(payload)

    @classmethod
    def deserialize(cls, payload: typing.Mapping[str, str]) -> "UnrecognisedAuditLogEntryInfo":
        return cls(payload)


def get_entry_info_entity(type_: int) -> typing.Type[BaseAuditLogEntryInfo]:
    """Get the entity that's registered for an entry's options.

    Parameters
    ----------
    type_ : int
        The identifier for this entry type.

    Returns
    -------
    typing.Type [ BaseAuditLogEntryInfo ]
        The associated options entity. If not implemented then this will be
        UnrecognisedAuditLogEntryInfo`
    """
    types = getattr(register_audit_log_entry_info, "types", more_collections.EMPTY_DICT)
    entry_type = types.get(type_)
    return entry_type if entry_type is not None else UnrecognisedAuditLogEntryInfo


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class AuditLogEntry(bases.UniqueEntity, marshaller.Deserializable):
    """Represents an entry in a guild's audit log.

    Attributes
    ----------
    target_id : hikari.snowflakes.Snowflake, optional
        The ID of the entity affected by this change, if applicable.
    changes : typing.Sequence [ AuditLogChange ]
        A sequence of the changes made to `AuditLogEntry.target_id`.
    user_id : hikari.snowflakes.Snowflake
        The ID of the user who made this change.
    action_type : typing.Union [ AuditLogEventType, str ]
        The type of action this entry represents.
    options : BaseAuditLogEntryInfo, optional
        Extra information about this entry. Will only be provided for certain
        `action_type`.
    reason : str, optional
        The reason for this change, if set (between 0-512 characters).
    """

    target_id: typing.Optional[bases.Snowflake] = marshaller.attrib()
    changes: typing.Sequence[AuditLogChange] = marshaller.attrib()
    user_id: bases.Snowflake = marshaller.attrib()
    action_type: typing.Union[AuditLogEventType, str] = marshaller.attrib()
    options: typing.Optional[BaseAuditLogEntryInfo] = marshaller.attrib()
    reason: typing.Optional[str] = marshaller.attrib()

    @classmethod
    def deserialize(cls, payload: typing.Mapping[str, str]) -> "AuditLogEntry":
        """Deserialize this model from a raw payload."""
        action_type = conversions.try_cast(payload["action_type"], AuditLogEventType, payload["action_type"])
        if target_id := payload.get("target_id"):
            target_id = bases.Snowflake.deserialize(target_id)

        if (options := payload.get("options")) is not None:
            if option_converter := get_entry_info_entity(action_type):
                options = option_converter.deserialize(options)

        # noinspection PyArgumentList
        return cls(
            target_id=target_id,
            changes=[
                AuditLogChange.deserialize(payload)
                for payload in payload.get("changes", more_collections.EMPTY_SEQUENCE)
            ],
            user_id=bases.Snowflake.deserialize(payload["user_id"]),
            id=bases.Snowflake.deserialize(payload["id"]),
            action_type=action_type,
            options=options,
            reason=payload.get("reason"),
        )


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class AuditLog(bases.HikariEntity, marshaller.Deserializable):
    """Represents a guilds audit log.

    Attributes
    ----------
    entries : typing.Mapping [ hikari.snowflakes.Snowflake, AuditLogEntry ]
        A sequence of the audit log's entries.
    integrations : typing.Mapping [ hikari.snowflakes.Snowflake, hikari.guilds.GuildIntegration ]
        A mapping of the partial objects of integrations found in this audit log.
    users : typing.Mapping [ hikari.bases.Snowflake, hikari.users.User` ]
        A mapping of the objects of users found in this audit log.
    webhooks : typing.Mapping [ hikari.snowflakes.Snowflake, hikari.webhooks.Webhook ]
        A mapping of the objects of webhooks found in this audit log.
    """
    entries: typing.Mapping[bases.Snowflake, AuditLogEntry] = marshaller.attrib(
        raw_name="audit_log_entries",
        deserializer=lambda payload: {entry.id: entry for entry in map(AuditLogEntry.deserialize, payload)},
    )
    integrations: typing.Mapping[bases.Snowflake, guilds.GuildIntegration] = marshaller.attrib(
        deserializer=lambda payload: {
            integration.id: integration for integration in map(guilds.PartialGuildIntegration.deserialize, payload)
        }
    )
    users: typing.Mapping[bases.Snowflake, _users.User] = marshaller.attrib(
        deserializer=lambda payload: {user.id: user for user in map(_users.User.deserialize, payload)}
    )
    webhooks: typing.Mapping[bases.Snowflake, _webhooks.Webhook] = marshaller.attrib(
        deserializer=lambda payload: {webhook.id: webhook for webhook in map(_webhooks.Webhook.deserialize, payload)}
    )


class AuditLogIterator(typing.AsyncIterator[AuditLogEntry]):
    """An async iterator used for iterating through a guild's audit log entries.

    This returns the audit log entries created before a given entry object/ID or
    from the newest audit log entry to the oldest.

    Attributes
    ----------
    integrations : typing.Mapping [ hikari.snowflakes.Snowflake, hikari.guilds.GuildIntegration ]
        A mapping of the partial objects of integrations found in this audit log
        so far.
    users : typing.Mapping [ hikari.snowflakes.Snowflake, hikari.users.User ]
        A mapping of the objects of users found in this audit log so far.
    webhooks : typing.Mapping [ hikari.snowflakes.Snowflake, hikari.webhooks.Webhook ]
        A mapping of the objects of webhooks found in this audit log so far.

    Parameters
    ----------
    guild_id : str
        The guild ID to look up.
    request : typing.Callable [ `...`, typing.Coroutine [ typing.Any, typing.Any, typing.Any ] ]
        The session bound function that this iterator should use for making
        Get Guild Audit Log requests.
    user_id : str
        If specified, the user ID to filter by.
    action_type : int
        If specified, the action type to look up.
    limit : int
        If specified, the limit to how many entries this iterator should return
        else unlimited.
    before : str
        If specified, an entry ID to specify where this iterator's returned
        audit log entries should start .

    Note
    ----
    This iterator's attributes `AuditLogIterator.integrations`,
    `AuditLogIterator.users` and `AuditLogIterator.webhooks` will be filled up
    as this iterator makes requests to the Get Guild Audit Log endpoint with
    the relevant objects for entities referenced by returned entries.
    """

    __slots__ = (
        "_buffer",
        "_front",
        "_kwargs",
        "_limit",
        "_request",
        "integrations",
        "users",
        "webhooks",
    )

    integrations: typing.Mapping[bases.Snowflake, guilds.GuildIntegration]
    users: typing.Mapping[bases.Snowflake, _users.User]
    webhooks: typing.Mapping[bases.Snowflake, _webhooks.Webhook]

    def __init__(
        self,
        guild_id: str,
        request: typing.Callable[..., more_typing.Coroutine[typing.Any]],
        before: typing.Optional[str] = None,
        user_id: str = ...,
        action_type: int = ...,
        limit: typing.Optional[int] = None,
    ) -> None:
        self._kwargs = {"guild_id": guild_id, "user_id": user_id, "action_type": action_type}
        self._limit = limit
        self._buffer = []
        self._request = request
        self._front = before
        self.users = {}
        self.webhooks = {}
        self.integrations = {}

    def __aiter__(self) -> "AuditLogIterator":
        return self

    async def __anext__(self) -> AuditLogEntry:
        if not self._buffer and self._limit != 0:
            await self._fill()
        try:
            entry = AuditLogEntry.deserialize(self._buffer.pop())
            self._front = str(entry.id)
            return entry
        except IndexError:
            raise StopAsyncIteration

    async def _fill(self) -> None:
        """Retrieve entries before :attr:`_front` and add to :attr:`_buffer`."""
        payload = await self._request(
            **self._kwargs,
            before=self._front if self._front is not None else ...,
            limit=100 if self._limit is None or self._limit > 100 else self._limit,
        )
        if self._limit is not None:
            self._limit -= len(payload["audit_log_entries"])

        # Once the resources has been exhausted, discord will return empty lists.
        payload["audit_log_entries"].reverse()
        self._buffer.extend(payload["audit_log_entries"])
        if users := payload.get("users"):
            self.users = copy.copy(self.users)
            self.users.update({u.id: u for u in map(_users.User.deserialize, users)})
        if webhooks := payload.get("webhooks"):
            self.webhooks = copy.copy(self.webhooks)
            self.webhooks.update({w.id: w for w in map(_webhooks.Webhook.deserialize, webhooks)})
        if integrations := payload.get("integrations"):
            self.integrations = copy.copy(self.integrations)
            self.integrations.update({i.id: i for i in map(guilds.PartialGuildIntegration.deserialize, integrations)})
