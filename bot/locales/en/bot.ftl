help =
  !!!THIS IS HELP MESSAGE BUT UNIMPLEMENTED!!!


rules =
  !!!THIS IS RULES MESSAGE BUT UNIMPLEMENTED!!!


create_game_text = 
  to create a new game send /start in this chat ᓚ₍ ^. .^₎


join-group = 
  bot is added to this <b>{$group_type}</b> with id <b>{$group_id}</b>

  {create_game_text}

join-user =
  your game id is: <b>{$game_id}</b>, to leave send /leave

join-user-group =
  <b>{$name}</b> has joined the game


start-group = 
  the game has been created, press the button below to join or send /start to start the game

start-group-button =
  join the game

start-user-help =
  to start using this bot add it to a groupchat and send /start


leave-group =
  bye bye

leave-user =
  you left the game with id {$game_id}

leave-user-group =
  {$name} has left the game

leave-user-invalid =
  you are not in any games


leave-group-user =
  the game you joined has been deleted because the bot has been kicked from the group


leave-user =
  !!!NOT IMPLEMENTED!!!


cancel-group = 
  the game has been canceled, to start a new one send /start

cancel-user = 
  the game you joined has been canceled, you are currently not in any game


start-group-game =
  the game has been started


not_enough_players =
  not enough players to start the game, you need at least <b>{$minimum_players}</b> players


rules =
  !!!HERE MUST BE THE GAME'S RULES. IMPLEMENT IT LATER!!!


round-info =
  round number <b>#{$round}</b>
  alive players:
  {$players}


request_money-group =
  now send me in a <b><u>user chat</u></b> the amount of money you want to request

request_money-user =
  <b>{$name}</b>, send me the amount of money you want to get, but not more than the bank: <b>{$bank}</b>


got_request-group =
  <b>{$name}</b> has requested the money succesfully

got_request-user =
  you have requested <b>{$request}</b> succesfully

got_request-user-invalid =
  you can't request less than zero or more than the bank


all_requested-group =
  everyone has requested the money


response-group =
  everyone has got what they deserved !&gt;.&lt;!

response-user =
  you requested for <b>{$request}</b> and got <b>{$response}</b>


vote-group =
  now select in a <b><u>user chat</u></b> who you want to kick and how much money you want to spend on the kick

vote-user =
  now select the player you want to <b>kick</b>:

vote-button-done =
  finish voting


voted-group =
  everyone has voted

voted-group-user =
  <b>{$name}</b> has voted

voted-user-player =
  you have voted for <b>{$player}</b>
  now send me the amount of money you want to spend to kick this player, you have <b>{$money}$</b>

voted-user-amount =
  you have voted succesfully!!

voted-user-amount-invalid =
  you can't spend more than you have or less than zero /ᐠ-ꞈ-ᐟ\

voted-user-more =
  you still have <b>{$money}$</b> left, so you can spend it


lost_players =
  lost players:
  {$lost_players}

lost-user =
  you have lost this game /ᐠﹷ ‸ ﹷ ᐟ\ﾉ
  now you can spectate other players


win-group =
  <b>{$name}</b> has won the game /ᐠ &gt; ˕ &lt;マ!!!

win-user =
  you have won this game ദ്ദി（• ˕ •マ.ᐟ


round_info = 
  ⭕️ <b>ROUND #{$round}</b>
    ├⎯⎯⎯⎯⎯⎯
    ├ bank: <b>{$bank}$</b>
    ├ players: <b>{$players}</b>
    ╰ lost: <b>{$lost}</b>

end_game-group =
  the game is over /ᐠ｡ꞈ｡ᐟ\

end_game-user =
  <b>{$name}</b>, the game is over so now you are not in this game lobby