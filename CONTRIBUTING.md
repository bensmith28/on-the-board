# Contributing to On The Board

Thanks for your interest in contributing! Here's how to get started.

## How to Contribute

1. Fork the repository and create a branch for your change.
2. Make your changes, with clear commit messages.
3. Open a pull request describing what you changed and why.

## Developer Certificate of Origin (DCO)

This project requires all commits to be signed off under the
[Developer Certificate of Origin (DCO)](https://developercertificate.org/).

The DCO is a lightweight way for you to certify that you wrote the code you're
contributing, or otherwise have the right to submit it under this project's
license (AGPL-3.0).

**To sign off on a commit**, add the `-s` flag when committing:

```bash
git commit -s -m "Your commit message"
```

This appends a line to your commit message:

```
Signed-off-by: Your Name your.email@example.com
```

Use your real name and a valid email address — anonymous or pseudonymous
sign-offs aren't accepted, since the point is to have a real identity attached
to the certification.

**If you forget to sign off**, you can fix your most recent commit with:

```bash
git commit --amend -s
```

For multiple commits in a PR, you can sign off all of them retroactively with:

```bash
git rebase --signoff HEAD~<number-of-commits>
```

Then force-push to update your PR branch:

```bash
git push --force-with-lease
```

Pull requests with unsigned commits will be blocked from merging until this is fixed.

## License

By contributing, you agree that your contributions will be licensed under the
project's [AGPL-3.0 license](./LICENSE).
