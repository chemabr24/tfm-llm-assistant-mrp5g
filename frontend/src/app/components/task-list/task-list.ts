import { Component, Input, Output, EventEmitter, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatChipsModule } from '@angular/material/chips';
import { MatDividerModule } from '@angular/material/divider';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { ChatService } from '../../services/chat.service';
import { Task, Document } from '../../models/chat.models';

@Component({
  selector: 'app-task-list',
  standalone: true,
  imports: [
    CommonModule,
    MatListModule,
    MatIconModule,
    MatButtonModule,
    MatTooltipModule,
    MatChipsModule,
    MatDividerModule,
    MatButtonToggleModule
  ],
  templateUrl: './task-list.html',
  styleUrl: './task-list.scss'
})
export class TaskListComponent {

  @Input() set tasks(value: Task[]) {
    this._allTasks.set(value);
  }

  @Input() set documents(value: Document[]) {
    this._documents.set(value);
  }

  @Output() taskUpdated = new EventEmitter<void>();

  _allTasks = signal<Task[]>([]);
  _documents = signal<Document[]>([]);
  activeFilter = signal<string>('pending');

  filteredTasks() {
    return this._allTasks().filter(t => t.status === this.activeFilter());
  }

  constructor(private chatService: ChatService) {}

  setFilter(filter: string): void {
    this.activeFilter.set(filter);
  }

  completeTask(taskId: string): void {
    this.chatService.updateTask(taskId, 'completed').subscribe({
      next: () => {
        this._allTasks.update(tasks =>
          tasks.map(t => t.id === taskId ? { ...t, status: 'completed' } : t)
        );
        this.taskUpdated.emit();
      }
    });
  }

  archiveTask(taskId: string): void {
    this.chatService.updateTask(taskId, 'archived').subscribe({
      next: () => {
        this._allTasks.update(tasks =>
          tasks.map(t => t.id === taskId ? { ...t, status: 'archived' } : t)
        );
        this.taskUpdated.emit();
      }
    });
  }

  openDocument(documentId: string): void {
    const url = this.chatService.getDocumentUrl(documentId);
    window.open(url, '_blank');
  }
}