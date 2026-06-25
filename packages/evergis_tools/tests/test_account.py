# -*- coding: utf-8 -*-
"""Unit tests for evergis_tools.account -- auth, users, and roles helpers."""

from unittest.mock import MagicMock

import pytest

from evergis_api.schemas import (
    CreateRoleDc,
    CreateUserDc,
    LoginDc,
    LoginResultDc,
    RoleInfoDc,
    UpdateRoleDc,
    UpdateUserDc,
    UserInfoDc,
)

from evergis_tools.account import (
    create_role,
    iter_roles,
    iter_users,
    login_with_credentials,
    provision_user,
    set_roles,
    update_role,
    update_user,
)


# =====================================================================
# Helpers
# =====================================================================


def _make_client():
    """Build a MagicMock client with an ``account`` namespace attached."""
    client = MagicMock()
    client.account = MagicMock()
    return client


def _users_page(usernames, *, limit):
    """Build a mock paged response holding ``UserInfoDc`` items."""
    page = MagicMock()
    page.items = [UserInfoDc(username=u) for u in usernames]
    page.limit = limit
    page.offset = 0
    page.totalCount = len(usernames)
    return page


def _roles_page(names, *, limit):
    """Build a mock paged response holding ``RoleInfoDc`` items."""
    page = MagicMock()
    page.items = [RoleInfoDc(name=n) for n in names]
    page.limit = limit
    page.offset = 0
    page.totalCount = len(names)
    return page


# =====================================================================
# auth.login_with_credentials
# =====================================================================


class TestLoginWithCredentials:
    """Tests for login_with_credentials()."""

    def test_calls_authenticate_with_login_dc(self):
        client = _make_client()
        result = LoginResultDc(token="jwt-abc", username="alice")
        client.account.authenticate.return_value = result

        login_with_credentials(client, "alice", "s3cret")

        client.account.authenticate.assert_called_once()
        kwargs = client.account.authenticate.call_args.kwargs
        body = kwargs["body"]
        assert isinstance(body, LoginDc)
        assert body.username == "alice"
        assert body.password == "s3cret"

    def test_returns_full_login_result(self):
        client = _make_client()
        result = LoginResultDc(
            token="jwt-abc",
            refreshToken="refresh-xyz",
            username="alice",
            redirectUrl="/home",
        )
        client.account.authenticate.return_value = result

        returned = login_with_credentials(client, "alice", "s3cret")

        assert returned is result
        assert returned.token == "jwt-abc"
        assert returned.refreshToken == "refresh-xyz"

    def test_bearer_token_attached_to_client(self):
        client = _make_client()
        result = LoginResultDc(token="jwt-abc", username="alice")
        client.account.authenticate.return_value = result

        login_with_credentials(client, "alice", "s3cret")

        client.account.set_bearer_token.assert_called_once_with("jwt-abc")


# =====================================================================
# users.iter_users
# =====================================================================


class TestIterUsers:
    """Tests for iter_users()."""

    def test_single_page_short_circuit(self):
        client = _make_client()
        client.account.get_users.return_value = _users_page(
            ["a", "b"], limit=1000
        )

        out = list(iter_users(client))

        assert [u.username for u in out] == ["a", "b"]
        assert client.account.get_users.call_count == 1

    def test_pagination_across_multiple_pages(self):
        client = _make_client()
        page_size = 3
        # Two full pages + one short page -> 3 calls total.
        client.account.get_users.side_effect = [
            _users_page(["u1", "u2", "u3"], limit=page_size),
            _users_page(["u4", "u5", "u6"], limit=page_size),
            _users_page(["u7"], limit=page_size),
        ]

        out = list(iter_users(client, page_size=page_size))

        assert [u.username for u in out] == [
            "u1", "u2", "u3", "u4", "u5", "u6", "u7",
        ]
        assert client.account.get_users.call_count == 3

    def test_empty_first_page_stops_immediately(self):
        client = _make_client()
        client.account.get_users.return_value = _users_page([], limit=1000)

        out = list(iter_users(client))

        assert out == []
        assert client.account.get_users.call_count == 1

    def test_none_items_handled_gracefully(self):
        client = _make_client()
        empty_page = MagicMock()
        empty_page.items = None
        client.account.get_users.return_value = empty_page

        out = list(iter_users(client))

        assert out == []

    def test_filter_and_order_passed_through(self):
        client = _make_client()
        client.account.get_users.return_value = _users_page([], limit=1000)

        list(
            iter_users(
                client,
                filter="alice%",
                order_by="username",
                users=["alice", "bob"],
                roles=["admin"],
                page_size=50,
            )
        )

        kwargs = client.account.get_users.call_args.kwargs
        assert kwargs["filter"] == "alice%"
        assert kwargs["orderBy"] == "username"
        assert kwargs["users"] == ["alice", "bob"]
        assert kwargs["roles"] == ["admin"]
        assert kwargs["limit"] == 50
        assert kwargs["offset"] == 0

    def test_offset_advances_by_page_size(self):
        client = _make_client()
        page_size = 2
        client.account.get_users.side_effect = [
            _users_page(["a", "b"], limit=page_size),
            _users_page(["c"], limit=page_size),
        ]

        list(iter_users(client, page_size=page_size))

        offsets = [
            call.kwargs["offset"]
            for call in client.account.get_users.call_args_list
        ]
        assert offsets == [0, 2]


# =====================================================================
# users.set_roles
# =====================================================================


class TestSetRoles:
    """Tests for set_roles()."""

    def _stub_user_with_roles(self, client, roles):
        info = MagicMock()
        info.roles = list(roles)
        client.account.get_extended_user_info_1.return_value = info

    def test_returns_added_and_removed_sets(self):
        client = _make_client()
        self._stub_user_with_roles(client, ["editor", "viewer"])

        added, removed = set_roles(client, "alice", ["editor", "admin"])

        assert added == {"admin"}
        assert removed == {"viewer"}

    def test_same_set_makes_no_calls(self):
        client = _make_client()
        self._stub_user_with_roles(client, ["a", "b"])

        added, removed = set_roles(client, "alice", ["a", "b"])

        assert added == set()
        assert removed == set()
        client.account.add_to_role.assert_not_called()
        client.account.remove_from_role.assert_not_called()

    def test_empty_target_removes_all(self):
        client = _make_client()
        self._stub_user_with_roles(client, ["a", "b"])

        added, removed = set_roles(client, "alice", [])

        assert added == set()
        assert removed == {"a", "b"}
        client.account.add_to_role.assert_not_called()
        assert client.account.remove_from_role.call_count == 2

    def test_adds_when_user_has_no_roles(self):
        client = _make_client()
        self._stub_user_with_roles(client, [])

        added, removed = set_roles(client, "alice", ["a", "b"])

        assert added == {"a", "b"}
        assert removed == set()
        assert client.account.add_to_role.call_count == 2
        client.account.remove_from_role.assert_not_called()

    def test_handles_none_current_roles(self):
        client = _make_client()
        info = MagicMock()
        info.roles = None
        client.account.get_extended_user_info_1.return_value = info

        added, removed = set_roles(client, "alice", ["x"])

        assert added == {"x"}
        assert removed == set()

    def test_add_and_remove_use_role_kwargs(self):
        client = _make_client()
        self._stub_user_with_roles(client, ["old"])

        set_roles(client, "alice", ["new"])

        client.account.add_to_role.assert_called_once_with(
            username="alice", role="new"
        )
        client.account.remove_from_role.assert_called_once_with(
            username="alice", role="old"
        )


# =====================================================================
# users.update_user
# =====================================================================


class TestUpdateUser:
    """Tests for update_user()."""

    def _stub_current(self, client, **fields):
        info = MagicMock(spec=UserInfoDc)
        # Default all UpdateUserDc-compatible attributes to None so
        # hasattr() finds them but they don't smuggle in MagicMock values.
        for name in UpdateUserDc.model_fields:
            setattr(info, name, None)
        info.username = "alice"
        for k, v in fields.items():
            setattr(info, k, v)
        client.account.get_extended_user_info_1.return_value = info
        # update_user returns the post-update info via get_user_info_1.
        client.account.get_user_info_1.return_value = UserInfoDc(
            username="alice", **{
                k: v for k, v in fields.items()
                if k in UserInfoDc.model_fields
            },
        )

    def test_calls_update_with_full_body(self):
        client = _make_client()
        self._stub_current(
            client, email="old@x.com", first_name="Al", last_name="Ice"
        )

        update_user(client, "alice", email="new@x.com")

        client.account.update_user.assert_called_once()
        body = client.account.update_user.call_args.kwargs["body"]
        assert isinstance(body, UpdateUserDc)
        assert body.username == "alice"
        assert body.email == "new@x.com"
        # Unmodified fields are preserved from the current state.
        assert body.first_name == "Al"
        assert body.last_name == "Ice"

    def test_only_overrides_specified_field(self):
        client = _make_client()
        self._stub_current(
            client, email="keep@x.com", phone="+1", is_active=True
        )

        update_user(client, "alice", phone="+9")

        body = client.account.update_user.call_args.kwargs["body"]
        assert body.phone == "+9"
        assert body.email == "keep@x.com"
        assert body.is_active is True

    def test_returns_refreshed_user_info(self):
        client = _make_client()
        self._stub_current(client, email="old@x.com")

        refreshed = UserInfoDc(username="alice", email="new@x.com")
        client.account.get_user_info_1.return_value = refreshed

        out = update_user(client, "alice", email="new@x.com")

        assert out is refreshed
        client.account.get_user_info_1.assert_called_once_with(
            username="alice"
        )

    def test_fetches_current_state_first(self):
        client = _make_client()
        self._stub_current(client, email="old@x.com")

        update_user(client, "alice", email="new@x.com")

        client.account.get_extended_user_info_1.assert_called_once_with(
            username="alice"
        )


# =====================================================================
# users.provision_user
# =====================================================================


class TestProvisionUser:
    """Tests for provision_user()."""

    def test_creates_user_when_missing(self):
        client = _make_client()
        client.account.is_username_exists.return_value = False
        client.account.get_user_info_1.return_value = UserInfoDc(
            username="alice"
        )

        provision_user(
            client, "alice", "pw", "a@x.com",
            first_name="Al", last_name="Ice",
        )

        client.account.create_user.assert_called_once()
        kwargs = client.account.create_user.call_args.kwargs
        body = kwargs["body"]
        assert isinstance(body, CreateUserDc)
        assert body.username == "alice"
        assert body.password == "pw"
        assert body.email == "a@x.com"
        assert body.first_name == "Al"
        assert body.last_name == "Ice"
        assert kwargs["sendConfirmEmail"] is False
        assert kwargs["createNamespace"] is True

    def test_creates_then_adds_roles(self):
        client = _make_client()
        client.account.is_username_exists.return_value = False
        client.account.get_user_info_1.return_value = UserInfoDc(
            username="alice"
        )

        provision_user(
            client, "alice", "pw", "a@x.com", roles=["admin", "editor"]
        )

        # Created exactly once, then add_to_role called per requested role.
        client.account.create_user.assert_called_once()
        assert client.account.add_to_role.call_count == 2
        calls = client.account.add_to_role.call_args_list
        called_roles = {c.kwargs["role"] for c in calls}
        assert called_roles == {"admin", "editor"}
        for c in calls:
            assert c.kwargs["username"] == "alice"

    def test_existing_user_skips_create_and_reconciles_roles(self):
        client = _make_client()
        client.account.is_username_exists.return_value = True
        # set_roles path -> get_extended_user_info_1 must return roles list.
        ext = MagicMock()
        ext.roles = ["viewer"]
        client.account.get_extended_user_info_1.return_value = ext
        client.account.get_user_info_1.return_value = UserInfoDc(
            username="alice"
        )

        provision_user(client, "alice", "pw", "a@x.com", roles=["admin"])

        client.account.create_user.assert_not_called()
        # set_roles reconciles: add admin, remove viewer.
        client.account.add_to_role.assert_called_once_with(
            username="alice", role="admin"
        )
        client.account.remove_from_role.assert_called_once_with(
            username="alice", role="viewer"
        )

    def test_existing_user_with_roles_none_leaves_roles_alone(self):
        client = _make_client()
        client.account.is_username_exists.return_value = True
        client.account.get_user_info_1.return_value = UserInfoDc(
            username="alice"
        )

        provision_user(client, "alice", "pw", "a@x.com", roles=None)

        client.account.create_user.assert_not_called()
        client.account.get_extended_user_info_1.assert_not_called()
        client.account.add_to_role.assert_not_called()
        client.account.remove_from_role.assert_not_called()

    def test_create_user_without_roles_does_not_add_roles(self):
        client = _make_client()
        client.account.is_username_exists.return_value = False
        client.account.get_user_info_1.return_value = UserInfoDc(
            username="alice"
        )

        provision_user(client, "alice", "pw", "a@x.com")

        client.account.create_user.assert_called_once()
        client.account.add_to_role.assert_not_called()

    @pytest.mark.parametrize("with_namespace", [True, False])
    def test_create_namespace_flag_propagates(self, with_namespace):
        client = _make_client()
        client.account.is_username_exists.return_value = False
        client.account.get_user_info_1.return_value = UserInfoDc(
            username="alice"
        )

        provision_user(
            client, "alice", "pw", "a@x.com",
            with_namespace=with_namespace,
        )

        kwargs = client.account.create_user.call_args.kwargs
        assert kwargs["createNamespace"] is with_namespace

    def test_returns_user_info(self):
        client = _make_client()
        client.account.is_username_exists.return_value = False
        expected = UserInfoDc(username="alice", email="a@x.com")
        client.account.get_user_info_1.return_value = expected

        out = provision_user(client, "alice", "pw", "a@x.com")

        assert out is expected


# =====================================================================
# roles.iter_roles
# =====================================================================


class TestIterRoles:
    """Tests for iter_roles()."""

    def test_single_page_short_circuit(self):
        client = _make_client()
        client.account.get_roles.return_value = _roles_page(
            ["admin", "viewer"], limit=1000
        )

        out = list(iter_roles(client))

        assert [r.name for r in out] == ["admin", "viewer"]
        assert client.account.get_roles.call_count == 1

    def test_pagination_across_pages(self):
        client = _make_client()
        page_size = 2
        client.account.get_roles.side_effect = [
            _roles_page(["r1", "r2"], limit=page_size),
            _roles_page(["r3", "r4"], limit=page_size),
            _roles_page(["r5"], limit=page_size),
        ]

        out = list(iter_roles(client, page_size=page_size))

        assert [r.name for r in out] == ["r1", "r2", "r3", "r4", "r5"]
        assert client.account.get_roles.call_count == 3

    def test_empty_items_returns_empty(self):
        client = _make_client()
        empty_page = MagicMock()
        empty_page.items = None
        client.account.get_roles.return_value = empty_page

        assert list(iter_roles(client)) == []

    def test_filter_and_user_filter_propagated(self):
        client = _make_client()
        client.account.get_roles.return_value = _roles_page([], limit=1000)

        list(
            iter_roles(
                client,
                filter="adm%",
                user_filter="ali%",
                order_by="name",
                with_system=True,
                page_size=25,
            )
        )

        kwargs = client.account.get_roles.call_args.kwargs
        assert kwargs["filter"] == "adm%"
        assert kwargs["userFilter"] == "ali%"
        assert kwargs["orderBy"] == "name"
        assert kwargs["withSystem"] is True
        assert kwargs["limit"] == 25
        assert kwargs["offset"] == 0


# =====================================================================
# roles.create_role
# =====================================================================


class TestCreateRole:
    """Tests for create_role()."""

    def test_calls_create_with_create_role_dc(self):
        client = _make_client()
        # _find_role iterates roles after creation -> stub it.
        client.account.get_roles.return_value = _roles_page(
            ["admin"], limit=1000
        )

        create_role(
            client, "admin",
            alias="Administrator", description="Full access",
        )

        client.account.create_role.assert_called_once()
        body = client.account.create_role.call_args.kwargs["body"]
        assert isinstance(body, CreateRoleDc)
        assert body.name == "admin"
        assert body.alias == "Administrator"
        assert body.description == "Full access"

    def test_returns_role_info_after_create(self):
        client = _make_client()
        client.account.get_roles.return_value = _roles_page(
            ["admin"], limit=1000
        )

        out = create_role(client, "admin")

        assert isinstance(out, RoleInfoDc)
        assert out.name == "admin"

    def test_raises_when_role_disappeared(self):
        client = _make_client()
        # Listing returns nothing -> _find_role returns None.
        client.account.get_roles.return_value = _roles_page([], limit=1000)

        with pytest.raises(RuntimeError, match="not found after create"):
            create_role(client, "admin")

    def test_optional_args_default_to_none(self):
        client = _make_client()
        client.account.get_roles.return_value = _roles_page(
            ["admin"], limit=1000
        )

        create_role(client, "admin")

        body = client.account.create_role.call_args.kwargs["body"]
        assert body.alias is None
        assert body.description is None


# =====================================================================
# roles.update_role
# =====================================================================


class TestUpdateRole:
    """Tests for update_role()."""

    def _stub_existing(self, client, name, alias=None):
        """Two ``get_roles`` calls happen: one for _find_role pre-update,
        one for _find_role post-update."""
        page_pre = MagicMock()
        page_pre.items = [RoleInfoDc(name=name, alias=alias)]
        page_post = MagicMock()
        page_post.items = [RoleInfoDc(name=name, alias=alias)]
        client.account.get_roles.side_effect = [page_pre, page_post]

    def test_calls_update_with_merged_body(self):
        client = _make_client()
        self._stub_existing(client, "admin", alias="Administrator")

        update_role(client, "admin", description="Full access")

        client.account.update_role.assert_called_once()
        body = client.account.update_role.call_args.kwargs["body"]
        assert isinstance(body, UpdateRoleDc)
        assert body.old_name == "admin"
        assert body.name == "admin"
        # alias preserved from the current role record.
        assert body.alias == "Administrator"
        assert body.description == "Full access"

    def test_alias_preserved_when_not_overridden(self):
        client = _make_client()
        self._stub_existing(client, "admin", alias="Boss")

        update_role(client, "admin", description="x")

        body = client.account.update_role.call_args.kwargs["body"]
        assert body.alias == "Boss"

    def test_alias_overridden_when_passed(self):
        client = _make_client()
        page_pre = MagicMock()
        page_pre.items = [RoleInfoDc(name="admin", alias="OldAlias")]
        page_post = MagicMock()
        page_post.items = [RoleInfoDc(name="admin", alias="NewAlias")]
        client.account.get_roles.side_effect = [page_pre, page_post]

        update_role(client, "admin", alias="NewAlias")

        body = client.account.update_role.call_args.kwargs["body"]
        assert body.alias == "NewAlias"

    def test_old_name_matches_current_name(self):
        client = _make_client()
        self._stub_existing(client, "admin", alias="A")

        update_role(client, "admin", description="updated")

        body = client.account.update_role.call_args.kwargs["body"]
        # ``old_name`` is the lookup key, ``name`` defaults to current name.
        assert body.old_name == "admin"
        assert body.name == "admin"

    def test_raises_when_role_missing(self):
        client = _make_client()
        client.account.get_roles.return_value = _roles_page([], limit=1000)

        with pytest.raises(ValueError, match="not found"):
            update_role(client, "ghost", alias="x")

        client.account.update_role.assert_not_called()

    def test_raises_when_role_disappears_after_update(self):
        client = _make_client()
        page_pre = MagicMock()
        page_pre.items = [RoleInfoDc(name="admin", alias="A")]
        page_post = MagicMock()
        page_post.items = []  # role missing post-update
        client.account.get_roles.side_effect = [page_pre, page_post]

        with pytest.raises(RuntimeError, match="disappeared after update"):
            update_role(client, "admin", description="x")
