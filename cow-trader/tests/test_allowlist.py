import ape
import pytest


# Gnosis chain token addresses
class TokenAddresses:
    GNO = "0x9C58BAcC331c9aa871AFD802DB6379a98e80CEdb"
    COW = "0x177127622c4A00F3d409B75571e12cB3c8973d3c"
    WETH = "0x6A023CCd1ff6F2045C3309768eAd9E68F978f6e1"
    SAFE = "0x5aFE3855358E112B5647B952709E6165e1c1eEEe"


@pytest.fixture
def tokens():
    return TokenAddresses()


@pytest.fixture
def token_batch(tokens):
    return [tokens.GNO, tokens.COW, tokens.WETH, tokens.SAFE]


@pytest.fixture
def owner(accounts):
    return accounts[0]


@pytest.fixture
def not_owner(accounts):
    return accounts[1]


@pytest.fixture
def allowlist_contract(owner, project):
    return owner.deploy(project.TokenAllowlist)


@pytest.fixture
def populated_allowlist(allowlist_contract, owner, token_batch):
    allowlist_contract.addTokensBatch(token_batch, sender=owner)
    return allowlist_contract


def test_add_token(allowlist_contract, tokens, owner, not_owner):
    allowlist_contract.addToken(tokens.GNO, sender=owner)
    allowed = allowlist_contract.isAllowed(tokens.GNO)
    assert allowed is True

    with ape.reverts():
        allowlist_contract.addToken(tokens.GNO, sender=not_owner)


def test_token_not_allowed(allowlist_contract, tokens, owner):
    allowlist_contract.addToken(tokens.GNO, sender=owner)
    allowed = allowlist_contract.isAllowed(tokens.COW)
    assert allowed is False


def test_add_batch_tokens(allowlist_contract, token_batch, owner, not_owner):
    allowlist_contract.addTokensBatch(token_batch, sender=owner)
    for token in token_batch:
        allowed = allowlist_contract.isAllowed(token)
        assert allowed is True

    with ape.reverts():
        allowlist_contract.addTokensBatch(token_batch, sender=not_owner)


def test_allowed_tokens(allowlist_contract, token_batch, owner):
    allowlist_contract.addTokensBatch(token_batch, sender=owner)
    allowed_tokens = allowlist_contract.allowedTokens()
    assert allowed_tokens == token_batch


def test_remove_token(populated_allowlist, tokens, owner, not_owner):
    populated_allowlist.removeToken(tokens.GNO, sender=owner)
    allowed = populated_allowlist.isAllowed(tokens.GNO)
    assert allowed is False

    expected_tokens = [tokens.COW, tokens.WETH, tokens.SAFE]
    allowed_tokens = populated_allowlist.allowedTokens()
    assert set(allowed_tokens) == set(expected_tokens)

    with ape.reverts():
        populated_allowlist.removeToken(tokens.GNO, sender=not_owner)


def test_remove_batch_tokens(populated_allowlist, tokens, owner, not_owner):
    tokens_to_remove = [tokens.GNO, tokens.WETH]
    populated_allowlist.removeTokensBatch(tokens_to_remove, sender=owner)

    for token in tokens_to_remove:
        allowed = populated_allowlist.isAllowed(token)
        assert allowed is False

    remaining_tokens = [tokens.COW, tokens.SAFE]
    for token in remaining_tokens:
        allowed = populated_allowlist.isAllowed(token)
        assert allowed is True

    allowed_tokens = populated_allowlist.allowedTokens()
    assert set(allowed_tokens) == set(remaining_tokens)

    with ape.reverts():
        populated_allowlist.removeTokensBatch(tokens_to_remove, sender=not_owner)
