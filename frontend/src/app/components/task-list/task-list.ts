import { Component, Input, Output, EventEmitter, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatChipsModule } from '@angular/material/chips';
import { ChatService } from '../../services/chat.service';
import { Task } from '../../models/chat.models';

@Component({
  selector: 'app-task-list',
  standalone: true,
  imports: [
    CommonModule,
    MatListModule,
    MatIconModule,
    MatButtonModule,
    MatTooltipModule,
    MatChipsModule
  ],
  templateUrl: './task-list.html',
  styleUrl: './task-list.scss'
})
export class TaskListComponent {

  @Input() set tasks(value: Task[]) {
    this._tasks.set(value);
  }

  @Output() taskUpdated = new EventEmitter<void>();

  _tasks = signal<Task[]>([]);

  constructor(private chatService: ChatService) {}

  completeTask(taskId: string): void {
    this.chatService.updateTask(taskId, 'completed').subscribe({
      next: () => {
        this._tasks.update(tasks => tasks.filter(t => t.id !== taskId));
        this.taskUpdated.emit();
      }
    });
  }

  archiveTask(taskId: string): void {
    this.chatService.updateTask(taskId, 'archived').subscribe({
      next: () => {
        this._tasks.update(tasks => tasks.filter(t => t.id !== taskId));
        this.taskUpdated.emit();
      }
    });
  }
}