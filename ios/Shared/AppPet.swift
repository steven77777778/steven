import Foundation

/// 這個 app 是哪一隻桌寵。火星人和白色長耳是兩個獨立的 app（各自的安裝檔，互不覆蓋），
/// 共用同一份程式碼，用編譯旗標 BUNNY 區分：白色長耳的那個 app 編譯時會加上 BUNNY。
#if BUNNY
let isBunnyApp = true
#else
let isBunnyApp = false
#endif
