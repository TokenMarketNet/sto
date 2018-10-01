from corporategovernance.tests.utils import check_gas


def test_security_token_issue(chain, security_token, security_token_initial_supply, team_multisig, zero_address, customer):
    check_gas(chain, security_token.transact({"from": team_multisig}).issueTokens(security_token_initial_supply))
    assert security_token.call().totalSupply() == (security_token_initial_supply * 2)