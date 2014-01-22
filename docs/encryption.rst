Encrypted Settings
==================

If your yay config has a .gpg extension, Yay will attempt to decrypt it with GPG.

You would generate the .gpg version of a yay file using the GPG command line tools.

    $ gpg -e s00persekrit.yay

This will encrypt with public key / private key encryption. It will prompt you for
recipients. These are the GPG keys that can decrypt your secrets.

Your encrypted ``s00persekrit.yay.gpg`` might contain::

    sekrit:
      username: admin
      password: password55


You can reference this as though it is an ordinary .yay file::

    .includes:
      - s00persekrit.yay.gpg

    myothervariable: The password is {{sekrit.password}}.


