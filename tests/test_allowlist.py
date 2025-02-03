import pytest


# Gnosis chain token addresses
class TokenAddresses:
    GNO = "0x9C58BACC331C9AA871AFD802DB6379A98E80CEDB"
    COW = "0x177127622c4a00f3d409b75571e12cb3c8973d3c"
    WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
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
def allowlist_contract(owner, project):
    return owner.deploy(project.TokenAllowlist)


def test_add_token(owner, allowlist_contract, tokens):
    allowlist_contract.addToken(tokens.GNO, sender=owner)
    allowed = allowlist_contract.isAllowed(tokens.GNO)
    assert allowed is True


def test_token_not_allowed(owner, allowlist_contract, tokens):
    allowlist_contract.addToken(tokens.GNO, sender=owner)
    allowed = allowlist_contract.isAllowed(tokens.COW)
    assert allowed is False


def test_add_batch_tokens(owner, allowlist_contract, token_batch):
    allowlist_contract.addTokensBatch(token_batch, sender=owner)
    for token in token_batch:
        allowed = allowlist_contract.isAllowed(token)
        assert allowed is True
