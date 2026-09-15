using Microsoft.AspNetCore.Mvc;
using System.Diagnostics;
using WebApplication.Models;
using System.Collections.Generic;

namespace WebApplication.Controllers
{
    public class HomeController : Controller
    {
        //アプリケーション起動中にデータを保持するための簡易リスト
        public static Dictionary<int, TodoItem> TodoItems = new Dictionary<int, TodoItem>();
        

        [HttpGet]
        public IActionResult Index()
        {
            return View(TodoItems);
        }

        [HttpPost]
        public IActionResult AddTodoItem(int id, string title)
        {
            
            // 3. すでに同じIDが存在しないか確認（キー重複防止）
            if (!TodoItems.ContainsKey(id))
            {
                TodoItem todoItem = new TodoItem();
                todoItem.Id = id;
                todoItem.Title = title;

                TodoItems.Add(id, todoItem);
            }
            else
            {
                // 同じIDが既に存在する場合の処理（必要に応じてメッセージ等を出す）
                // 例: TodoItems[id] = todoItem; で上書きにすることも可能
                AddTodoItem((id + 1), title);
            }
            

            return RedirectToAction("Index");
        }

        [HttpPost]
        public IActionResult DeleteTodoItem(int id)
        {

            TodoItems.Remove(id);
            return RedirectToAction("Index");
        }

        public IActionResult Privacy()
        {
            return View();
        }

        [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
        public IActionResult Error()
        {
            return View(new ErrorViewModel { RequestId = Activity.Current?.Id ?? HttpContext.TraceIdentifier });
        }
    }
}
