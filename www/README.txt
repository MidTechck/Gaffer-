M.L26 offline
=============

1. Keep this whole "www" folder together (index.html, js, css, img, data).
2. On the phone, from Termux in this folder:

     python -m http.server 8765

   Open http://127.0.0.1:8765
   Chrome menu → Add to Home screen.

3. After the first load, the service worker stores the pack.
   You can play with the radio off. Accounts and careers stay on THIS phone.

Usernames
---------
Create account: if the name exists you get suggestions (name2, name_1).
Sign in: only works if that name was created here. It will not invent an account.

This offline build is a playable core (career, matches, table, news).
The full Termux Python game still has UCL tabs, market, coaches, rooms.
