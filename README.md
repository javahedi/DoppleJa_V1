DoppleJa Main Header V4
=======================
This patch adds one physical 76px-tall logo slot at the top of #app on the four signed-in main tabs.
It hides the original page-specific header and moves its real action button into the shared slot.
No changes to app.js or backend. Existing bottom navigation is untouched.

Install:
  unzip -o ~/Downloads/DoppleJa_Main_Header_V4.zip -d .
  python3 install_app_header_v4.py

Test in-browser at 320, 375, 425, and 768 px on Discover, Matches, Chats, Profile.
Test logout from each page. Detail page headers remain as-is.
This package is additive: if you need to roll back, remove the two v4 includes from index.html.
